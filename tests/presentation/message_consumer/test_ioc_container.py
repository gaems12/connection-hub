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
from connection_hub.presentation.message_consumer import ioc_container_factory


async def test_ioc_container(
    nats_config: NATSConfig,
    redis_config: RedisConfig,
):
    centrifugo_config = CentrifugoConfig(
        url="fake_url",
        api_key="fake_api_key",
    )
    lobby_mapper_config = LobbyMapperConfig(
        lobby_expires_in=timedelta(days=1),
    )
    game_mapper_config = GameMapperConfig(
        game_expires_in=timedelta(days=1),
    )
    lock_manager_config = LockManagerConfig(
        lock_expires_in=timedelta(seconds=3),
    )

    ioc_container_factory(
        centrifugo_config_factory=lambda: centrifugo_config,
        redis_config_factory=lambda: redis_config,
        lobby_mapper_config_factory=lambda: lobby_mapper_config,
        game_mapper_config_factory=lambda: game_mapper_config,
        lock_manager_config_factory=lambda: lock_manager_config,
        nats_config_factory=lambda: nats_config,
    )
