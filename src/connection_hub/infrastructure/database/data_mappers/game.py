# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = (
    "GameMapperConfig",
    "load_game_mapper_config",
    "GameMapper",
)

import json
from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable
from enum import StrEnum

from redis.asyncio.client import Redis, Pipeline

from connection_hub.domain import GameId, UserId, ConnectFourGame, Game
from connection_hub.application import GameGateway
from connection_hub.infrastructure.database.lock_manager import LockManager
from connection_hub.infrastructure.common_retort import CommonRetort
from connection_hub.infrastructure.utils import get_env_var, str_to_timedelta


class _GameType(StrEnum):
    CONNECT_FOUR = "connect_four"


def load_game_mapper_config() -> "GameMapperConfig":
    return GameMapperConfig(
        game_expires_in=get_env_var(
            key="GAME_MAPPER_GAME_EXPIRES_IN",
            value_factory=str_to_timedelta,
            default=timedelta(days=1),
        ),
    )


@dataclass(frozen=True, slots=True)
class GameMapperConfig:
    game_expires_in: timedelta


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

    async def by_id(
        self,
        game_id: GameId,
        *,
        acquire: bool = False,
    ) -> Game | None:
        pattern = self._pattern_to_find_game_by_id(game_id)
        keys = await self._keys_by_pattern(pattern=pattern, limit=1)
        if not keys:
            return None

        if acquire:
            await self._lock_manager.acquire(keys[0])

        game_as_json = await self._redis.get(keys[0])  # type: ignore
        if game_as_json:
            game_as_dict = json.loads(game_as_json)
            return self._dict_to_game(game_as_dict)

        return None

    async def by_player_id(
        self,
        player_id: UserId,
        *,
        acquire: bool = False,
    ) -> Game | None:
        pattern = self._pattern_to_find_game_by_player_id(player_id)
        keys = await self._keys_by_pattern(pattern=pattern, limit=1)
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
        # Delete old game, because new game might have
        # different user ids (user ids being part of the key).
        # This adds an extra request to redis, which could be
        # avoided by tracking changes to game and, as a
        # consequence, deleting it only if user ids have
        # changed. However, this is considered overkill for now.
        await self.delete(game)

        game_key = self._game_key_factory(
            game_id=game.id,
            player_ids=game.players,
        )

        game_as_dict = self._game_to_dict(game)
        game_as_json = json.dumps(game_as_dict)

        self._redis_pipeline.set(game_key, game_as_json)

    async def delete(self, game: Game) -> None:
        pattern = self._pattern_to_find_game_by_id(game.id)
        keys = await self._redis.keys(pattern)
        self._redis_pipeline.delete(*keys)

    def _dict_to_game(self, dict_: dict) -> Game:
        raw_game_type = dict_.get("type")
        if not raw_game_type:
            raise Exception(
                "Cannot convert dict to game: dict has no 'type' key.",
            )

        game_type = _GameType(raw_game_type)

        if game_type == _GameType.CONNECT_FOUR:
            return self._common_retort.load(dict_, ConnectFourGame)

    def _game_to_dict(self, game: Game) -> dict:
        game_as_dict = self._common_retort.dump(game)

        if isinstance(game, ConnectFourGame):
            game_as_dict["type"] = _GameType.CONNECT_FOUR

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
            f"{':'.join((player_id.hex for player_id in sorted_player_ids))}"
        )

    def _pattern_to_find_game_by_id(self, game_id: GameId) -> str:
        return f"games:id:{game_id.hex}:player_ids:*"

    def _pattern_to_find_game_by_player_id(self, player_id: UserId) -> str:
        return f"games:id:*:player_ids:*{player_id.hex}*"

    async def _keys_by_pattern(
        self,
        *,
        pattern: str,
        batch_size: int = 10,
        limit: int | None = None,
    ) -> list[str]:
        keys: list[str] = []

        if limit == 0:
            return keys

        async for key in self._redis.scan_iter(
            match=pattern,
            count=batch_size,
        ):
            keys.append(key)

            if limit and len(keys) >= limit:
                return keys

        return keys
