# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

__all__ = ("RedisTransactionManager",)

from redis.asyncio.client import Pipeline

from lobby.application import TransactionManager
from .lock_manager import LockManager


class RedisTransactionManager(TransactionManager):
    __slots__ = ("_redis_pipeline", "_lock_manager")

    def __init__(
        self,
        redis_pipeline: Pipeline,
        lock_manager: LockManager,
    ):
        self._redis_pipeline = redis_pipeline
        self._lock_manager = lock_manager

    async def commit(self) -> None:
        await self._redis_pipeline.execute()
        await self._lock_manager.release_all()
