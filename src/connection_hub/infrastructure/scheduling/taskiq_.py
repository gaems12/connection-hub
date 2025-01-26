# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from taskiq_redis import RedisScheduleSource

from four_in_a_row.infrastructure.redis_config import RedisConfig


def taskiq_redis_schedule_source_factory(
    redis_config: RedisConfig,
) -> RedisScheduleSource:
    return RedisScheduleSource(url=redis_config.url)
