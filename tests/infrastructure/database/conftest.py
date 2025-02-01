# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from typing import AsyncGenerator
from contextlib import asynccontextmanager

import pytest
from redis.asyncio.client import Redis, Pipeline

from connection_hub.infrastructure import (
    get_env_var,
    RedisConfig,
    redis_factory,
    redis_pipeline_factory,
)


@pytest.fixture(scope="function")
async def redis() -> AsyncGenerator[Redis, None]:
    redis_url = get_env_var("TEST_REDIS_URL")
    redis_config = RedisConfig(url=redis_url)

    ctx_manager = asynccontextmanager(redis_factory)
    async with ctx_manager(redis_config) as redis:
        yield redis


@pytest.fixture(scope="function")
async def redis_pipeline(redis: Redis) -> AsyncGenerator[Pipeline, None]:
    ctx_manager = asynccontextmanager(redis_pipeline_factory)
    async with ctx_manager(redis) as redis_pipeline:
        yield redis_pipeline


@pytest.fixture(scope="function")
async def clear_redis(redis: Redis) -> None:
    await redis.flushall()
