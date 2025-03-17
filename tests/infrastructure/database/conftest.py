# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from typing import AsyncGenerator

import pytest
from redis.asyncio.client import Redis, Pipeline

from connection_hub.infrastructure import (
    RedisConfig,
    redis_factory,
    redis_pipeline_factory,
)


@pytest.fixture(scope="function")
async def redis(redis_config: RedisConfig) -> AsyncGenerator[Redis, None]:
    async for redis in redis_factory(redis_config):
        yield redis


@pytest.fixture(scope="function")
async def redis_pipeline(redis: Redis) -> AsyncGenerator[Pipeline, None]:
    async for redis_pipeline in redis_pipeline_factory(redis):
        yield redis_pipeline


@pytest.fixture(scope="function")
async def clear_redis(redis: Redis) -> None:
    await redis.flushall()
