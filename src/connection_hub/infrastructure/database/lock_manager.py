# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

__all__ = (
    "LockManagerConfig",
    "lock_manager_config_from_env",
    "LockManager",
    "lock_manager_factory",
)

from dataclasses import dataclass
from datetime import timedelta
from typing import AsyncGenerator

from redis.asyncio.client import Redis

from connection_hub.infrastructure.utils import (
    get_env_var,
    str_to_timedelta,
)


def lock_manager_config_from_env() -> "LockManagerConfig":
    return LockManagerConfig(
        lock_expires_in=get_env_var(
            key="LOCK_EXPIRES_IN",
            value_factory=str_to_timedelta,
        ),
    )


@dataclass(frozen=True, slots=True)
class LockManagerConfig:
    lock_expires_in: timedelta


async def lock_manager_factory(
    redis: Redis,
    config: LockManagerConfig,
) -> AsyncGenerator["LockManager", None]:
    lock_manager = LockManager(redis=redis, config=config)
    yield lock_manager
    await lock_manager.release_all()


class LockManager:
    __slots__ = (
        "_redis",
        "_acquired_lock_names",
        "_config",
    )

    def __init__(self, redis: Redis, config: LockManagerConfig):
        self._redis = redis
        self._acquired_lock_names: list[str] = []
        self._config = config

    async def acquire(self, lock_id: str) -> None:
        """
        Acquires a lock with the specified ID.

        If the lock is already held by the current instance,
        it will return immediately. Otherwise, it waits until
        the lock becomes available and then acquires it.
        """
        lock_name = self._lock_name_factory(lock_id)
        if lock_name in self._acquired_lock_names:
            return

        lock_is_acquired = await self._redis.get(lock_name)
        while lock_is_acquired:
            lock_is_acquired = await self._redis.get(lock_name)

        await self._redis.set(
            name=lock_name,
            value="",
            ex=self._config.lock_expires_in,
        )
        self._acquired_lock_names.append(lock_name)

    async def release_all(self) -> None:
        if not self._acquired_lock_names:
            return

        await self._redis.delete(*self._acquired_lock_names)
        self._acquired_lock_names.clear()

    def _lock_name_factory(self, lock_id: str) -> str:
        return f"locks:{lock_id}"
