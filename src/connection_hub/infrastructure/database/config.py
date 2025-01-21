# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

__all__ = ("RedisConfig", "redis_config_from_env")

from dataclasses import dataclass

from connection_hub.infrastructure.utils import get_env_var


def redis_config_from_env() -> "RedisConfig":
    return RedisConfig(url=get_env_var("REDIS_URL"))


@dataclass(frozen=True, slots=True)
class RedisConfig:
    url: str
