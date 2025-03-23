# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from datetime import timedelta

from connection_hub.infrastructure import (
    CentrifugoConfig,
    RedisConfig,
    LobbyMapperConfig,
    GameMapperConfig,
    LockManagerConfig,
    NATSConfig,
)
from connection_hub.presentation.task_executor import ioc_container_factory


async def test_ioc_container(
    nats_config: NATSConfig,
    redis_config: RedisConfig,
):
    centrifugo_config = CentrifugoConfig(
        url="fake_url",
        api_key="fake_api_key",
    )
    lobby_mapper_config = LobbyMapperConfig(timedelta(days=1))
    game_mapper_config = GameMapperConfig(timedelta(days=1))
    lock_manager_config = LockManagerConfig(timedelta(seconds=3))

    context = {
        CentrifugoConfig: centrifugo_config,
        RedisConfig: redis_config,
        LobbyMapperConfig: lobby_mapper_config,
        GameMapperConfig: game_mapper_config,
        LockManagerConfig: lock_manager_config,
        NATSConfig: nats_config,
    }
    ioc_container_factory(context)
