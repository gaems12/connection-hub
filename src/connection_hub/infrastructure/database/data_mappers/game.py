# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

import json
from enum import StrEnum
from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable

from redis.asyncio.client import Redis, Pipeline

from connection_hub.domain import GameId, UserId, FourInARowGame, Game
from connection_hub.application import GameGateway
from connection_hub.infrastructure.database.lock_manager import LockManager
from connection_hub.infrastructure.common_retort import CommonRetort
from connection_hub.infrastructure.utils import get_env_var, str_to_timedelta


def game_mapper_config_from_env() -> "GameMapperConfig":
    return GameMapperConfig(
        game_expires_in=get_env_var(
            key="GAME_MAPPER_GAME_EXPIRES_IN",
            value_factory=str_to_timedelta,
        ),
    )


@dataclass(frozen=True, slots=True)
class GameMapperConfig:
    game_expires_in: timedelta


class _GameType(StrEnum):
    FOUR_IN_A_ROW = "four_in_a_row"


class GameMapper(GameGateway):
    __slots__ = (
        "_redis",
        "_redis_pipeline",
        "_common_retort",
        "_lock_manager",
        "_config",
    )

    def __init__(
        self,
        redis: Redis,
        redis_pipeline: Pipeline,
        common_retort: CommonRetort,
        lock_manager: LockManager,
        config: GameMapperConfig,
    ):
        self._redis = redis
        self._redis_pipeline = redis_pipeline
        self._common_retort = common_retort
        self._lock_manager = lock_manager
        self._config = config

    async def by_player_id(
        self,
        player_id: UserId,
        *,
        acquire: bool = False,
    ) -> Game | None:
        pattern = self._pattern_to_find_game_by_player_id(player_id)
        keys = await self._redis.keys(pattern)
        if not keys:
            return None

        if acquire:
            await self._lock_manager.acquire(keys[0])

        game_as_json = await self._redis.get(keys[0])  # type: ignore
        if game_as_json:
            game_as_dict = json.loads(game_as_json)
            return self._dict_to_game(game_as_dict)

        return None

    async def save(self, game: Game) -> None:
        game_key = self._game_key_factory(
            game_id=game.id,
            player_ids=game.players,
        )

        game_as_dict = self._game_to_dict(game)
        game_as_json = json.dumps(game_as_dict)

        self._redis_pipeline.set(
            name=game_key,
            value=game_as_json,
            ex=self._config.game_expires_in,
        )

    async def update(self, game: Game) -> None:
        game_key = self._game_key_factory(
            game_id=game.id,
            player_ids=game.players,
        )

        game_as_dict = self._game_to_dict(game)
        game_as_json = json.dumps(game_as_dict)

        self._redis_pipeline.set(game_key, game_as_json)

    def _dict_to_game(self, dict_: dict) -> Game:
        raw_game_type = dict_.get("type")
        if not raw_game_type:
            raise Exception("Cannot load game from None.")

        game_type = _GameType(raw_game_type)

        if game_type == _GameType.FOUR_IN_A_ROW:
            return self._common_retort.load(dict_, FourInARowGame)

    def _game_to_dict(self, game: Game) -> dict:
        game_as_dict = self._common_retort.dump(game)

        if isinstance(game, FourInARowGame):
            game_as_dict["type"] = _GameType.FOUR_IN_A_ROW

        return game_as_dict

    def _game_key_factory(
        self,
        *,
        game_id: GameId,
        player_ids: Iterable[UserId],
    ) -> str:
        sorted_player_ids = sorted(player_ids)
        return (
            f"games:id:{game_id.hex}:player_ids:"
            f"{":".join(map(lambda player_id: player_id.hex, sorted_player_ids))}"
        )

    def _pattern_to_find_game_by_player_id(self, player_id: UserId) -> str:
        return f"games:id:*:player_ids:*{player_id.hex}*"
