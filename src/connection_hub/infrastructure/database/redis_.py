# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

__all__ = ("redis_factory", "redis_pipeline_factory")

from typing import AsyncGenerator

from redis.asyncio.client import Redis, Pipeline

from connection_hub.infrastructure.redis_config import RedisConfig


async def redis_factory(
    config: RedisConfig,
) -> AsyncGenerator[Redis, None]:
    redis = Redis.from_url(url=config.url, decode_responses=True)
    yield redis
    await redis.aclose()


async def redis_pipeline_factory(
    redis: Redis,
) -> AsyncGenerator[Pipeline, None]:
    async with redis.pipeline() as pipeline:
        yield pipeline
