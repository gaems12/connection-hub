# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

import pytest

from connection_hub.infrastructure import RedisConfig, NATSConfig, get_env_var


@pytest.fixture(scope="session")
def redis_config() -> RedisConfig:
    redis_url = get_env_var("TEST_REDIS_URL")
    return RedisConfig(url=redis_url)


@pytest.fixture(scope="session")
def nats_config() -> NATSConfig:
    nats_url = get_env_var("TEST_NATS_URL")
    return NATSConfig(url=nats_url)
