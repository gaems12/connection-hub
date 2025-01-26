# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

__all__ = ("RedisConfig", "load_redis_config")

from dataclasses import dataclass

from connection_hub.infrastructure.utils import get_env_var


def load_redis_config() -> "RedisConfig":
    return RedisConfig(url=get_env_var("REDIS_URL"))


@dataclass(frozen=True, slots=True)
class RedisConfig:
    url: str
