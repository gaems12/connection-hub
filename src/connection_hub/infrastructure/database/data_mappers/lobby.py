# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

import json
from enum import StrEnum
from typing import Iterable
from dataclasses import dataclass
from datetime import timedelta

from redis.asyncio.client import Redis, Pipeline

from connection_hub.domain import LobbyId, UserId, FourInARowLobby, Lobby
from connection_hub.application import LobbyGateway
from connection_hub.infrastructure.database.lock_manager import LockManager
from connection_hub.infrastructure.common_retort import CommonRetort
from connection_hub.infrastructure.utils import get_env_var, str_to_timedelta


def lobby_mapper_config_from_env() -> "LobbyMapperConfig":
    return LobbyMapperConfig(
        lobby_expires_in=get_env_var(
            key="LOBBY_MAPPER_LOBBY_EXPIRES_IN",
            value_factory=str_to_timedelta,
        ),
    )


@dataclass(frozen=True, slots=True)
class LobbyMapperConfig:
    lobby_expires_in: timedelta


class _LobbyType(StrEnum):
    FOUR_IN_A_ROW = "four_in_a_row"


class LobbyMapper(LobbyGateway):
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
        config: LobbyMapperConfig,
    ):
        self._redis = redis
        self._redis_pipeline = redis_pipeline
        self._common_retort = common_retort
        self._lock_manager = lock_manager
        self._config = config

    async def by_id(
        self,
        id: LobbyId,
        *,
        acquire: bool = False,
    ) -> Lobby | None:
        if acquire:
            lock_id = self._lock_id_factory(id)
            await self._lock_manager.acquire(lock_id)

        pattern = self._pattern_to_find_lobby_by_id(id)
        keys = await self._redis.keys(pattern)
        if not keys:
            return None

        lobby_as_json = await self._redis.get(keys[0])  # type: ignore
        if lobby_as_json:
            lobby_as_dict = json.loads(lobby_as_json)
            return self._dict_to_lobby(lobby_as_dict)

        return None

    async def by_user_id(self, user_id: UserId) -> Lobby | None:
        pattern = self._pattern_to_find_lobby_by_user_id(user_id)
        keys = await self._redis.keys(pattern)
        if not keys:
            return None

        lobby_as_json = await self._redis.get(keys[0])  # type: ignore
        if lobby_as_json:
            lobby_as_dict = json.loads(lobby_as_json)
            return self._dict_to_lobby(lobby_as_dict)

        return None

    async def save(self, lobby: Lobby) -> None:
        lobby_key = self._lobby_key_factory(
            lobby_id=lobby.id,
            user_ids=lobby.users.keys(),
        )

        lobby_as_dict = self._lobby_to_dict(lobby)
        lobby_as_json = json.dumps(lobby_as_dict)

        self._redis_pipeline.set(
            name=lobby_key,
            value=lobby_as_json,
            ex=self._config.lobby_expires_in,
        )

    async def update(self, lobby: Lobby) -> None:
        # Delete old lobby, because new lobby might have
        # different user_ids (user_ids being part of the key).
        # This adds an extra request to redis, which could be
        # avoided by tracking changes to lobby and, as a
        # consequence, deleting it only if user_ids have
        # changed. However, this is considered overkill for now.
        await self.delete(lobby)

        lobby_key = self._lobby_key_factory(
            lobby_id=lobby.id,
            user_ids=lobby.users.keys(),
        )

        lobby_as_dict = self._lobby_to_dict(lobby)
        lobby_as_json = json.dumps(lobby_as_dict)

        self._redis_pipeline.set(lobby_key, lobby_as_json)

    async def delete(self, lobby: Lobby) -> None:
        lobby_key = self._lobby_key_factory(
            lobby_id=lobby.id,
            user_ids=lobby.users.keys(),
        )
        self._redis_pipeline.delete(lobby_key)

    def _dict_to_lobby(self, dict_: dict) -> Lobby:
        raw_lobby_type = dict_.get("type")
        if not raw_lobby_type:
            raise Exception("Cannot load lobby from None.")

        lobby_type = _LobbyType(raw_lobby_type)

        if lobby_type == _LobbyType.FOUR_IN_A_ROW:
            return self._common_retort.load(dict_, FourInARowLobby)

    def _lobby_to_dict(self, lobby: Lobby) -> dict:
        lobby_as_dict = self._common_retort.dump(lobby)

        if isinstance(lobby, FourInARowLobby):
            lobby_as_dict["type"] = _LobbyType.FOUR_IN_A_ROW

        return lobby_as_dict

    def _lobby_key_factory(
        self,
        *,
        lobby_id: LobbyId,
        user_ids: Iterable[UserId],
    ) -> str:
        sorted_user_ids = sorted(user_ids)
        return (
            f"lobbies:id:{lobby_id.hex}:user_ids:"
            f"{":".join(map(lambda user_id: user_id.hex, sorted_user_ids))}"
        )

    def _pattern_to_find_lobby_by_id(self, lobby_id: LobbyId) -> str:
        return f"lobbies:id:{lobby_id.hex}:user_ids:*"

    def _pattern_to_find_lobby_by_user_id(self, user_id: UserId) -> str:
        return f"lobbies:id:*:user_ids:*{user_id.hex}*"

    def _lock_id_factory(self, lobby_id: LobbyId) -> str:
        return f"lobbies:id:{lobby_id.hex}"
