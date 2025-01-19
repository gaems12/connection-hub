# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

import json
from enum import StrEnum
from dataclasses import dataclass
from datetime import timedelta

from redis.asyncio.client import Redis

from lobby.domain import UserId, FourInARowGame, Game
from lobby.application import GameGateway
from lobby.infrastructure.common_retort import CommonRetort
from lobby.infrastructure.utils import get_env_var, str_to_timedelta


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
        "_common_retort",
        "_config",
    )

    def __init__(
        self,
        redis: Redis,
        common_retort: CommonRetort,
        config: GameMapperConfig,
    ):
        self._redis = redis
        self._common_retort = common_retort
        self._config = config

    async def by_player_id(self, player_id: UserId) -> Game | None:
        pattern = self._pattern_to_find_game_by_player_id(player_id)
        keys = await self._redis.keys(pattern)
        if not keys:
            return None

        game_as_json = await self._redis.get(keys[0])  # type: ignore
        if game_as_json:
            game_as_dict = json.loads(game_as_json)
            return self._dict_to_game(game_as_dict)

        return None

    def _dict_to_game(self, dict_: dict) -> Game:
        raw_game_type = dict_.get("type")
        if not raw_game_type:
            raise Exception("Cannot load game from None.")

        game_type = _GameType(raw_game_type)

        if game_type == _GameType.FOUR_IN_A_ROW:
            return self._common_retort.load(dict_, FourInARowGame)

    def _pattern_to_find_game_by_player_id(self, player_id: UserId) -> str:
        return f"games:id:*:player_ids:*{player_id.hex}*"
