# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

import json
from enum import StrEnum
from typing import Iterable
from dataclasses import dataclass
from datetime import timedelta

from redis.asyncio.client import Redis, Pipeline

from connection_hub.domain import LobbyId, UserId, ConnectFourLobby, Lobby
from connection_hub.application import LobbyGateway
from connection_hub.infrastructure.database.lock_manager import LockManager
from connection_hub.infrastructure.common_retort import CommonRetort
from connection_hub.infrastructure.utils import get_env_var, str_to_timedelta


def load_lobby_mapper_config() -> "LobbyMapperConfig":
    return LobbyMapperConfig(
        lobby_expires_in=get_env_var(
            key="LOBBY_MAPPER_LOBBY_EXPIRES_IN",
            value_factory=str_to_timedelta,
            default=timedelta(days=1),
        ),
    )


@dataclass(frozen=True, slots=True)
class LobbyMapperConfig:
    lobby_expires_in: timedelta


class _LobbyType(StrEnum):
    CONNECT_FOUR = "connect_four"


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
        lobby_id: LobbyId,
        *,
        acquire: bool = False,
    ) -> Lobby | None:
        pattern = self._pattern_to_find_lobby_by_id(lobby_id)
        keys = await self._keys_by_pattern(pattern=pattern, limit=1)
        if not keys:
            return None

        if acquire:
            await self._lock_manager.acquire(keys[0])

        lobby_as_json = await self._redis.get(keys[0])  # type: ignore
        if lobby_as_json:
            lobby_as_dict = json.loads(lobby_as_json)
            return self._dict_to_lobby(lobby_as_dict)

        return None

    async def by_user_id(
        self,
        user_id: UserId,
        *,
        acquire: bool = False,
    ) -> Lobby | None:
        pattern = self._pattern_to_find_lobby_by_user_id(user_id)
        keys = await self._keys_by_pattern(pattern=pattern, limit=1)
        if not keys:
            return None

        if acquire:
            await self._lock_manager.acquire(keys[0])

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
        pattern = self._pattern_to_find_lobby_by_id(lobby.id)
        keys = await self._redis.keys(pattern)
        self._redis_pipeline.delete(*keys)

    def _dict_to_lobby(self, dict_: dict) -> Lobby:
        raw_lobby_type = dict_.get("type")
        if not raw_lobby_type:
            raise Exception(
                "Cannot convert dict to lobby: dict has no 'type' key.",
            )
        lobby_type = _LobbyType(raw_lobby_type)

        if lobby_type == _LobbyType.CONNECT_FOUR:
            return self._common_retort.load(dict_, ConnectFourLobby)

    def _lobby_to_dict(self, lobby: Lobby) -> dict:
        lobby_as_dict = self._common_retort.dump(lobby)

        if isinstance(lobby, ConnectFourLobby):
            lobby_as_dict["type"] = _LobbyType.CONNECT_FOUR

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
            f"{':'.join(map(lambda user_id: user_id.hex, sorted_user_ids))}"
        )

    def _pattern_to_find_lobby_by_id(self, lobby_id: LobbyId) -> str:
        return f"lobbies:id:{lobby_id.hex}:user_ids:*"

    def _pattern_to_find_lobby_by_user_id(self, user_id: UserId) -> str:
        return f"lobbies:id:*:user_ids:*{user_id.hex}*"

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
