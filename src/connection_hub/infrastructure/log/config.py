# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from dataclasses import dataclass

from connection_hub.infrastructure.utils import get_env_var


def load_logging_config() -> "LoggingConfig":
    return LoggingConfig(level=get_env_var("LOGGING_LEVEL", default="DEBUG"))


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    level: str
