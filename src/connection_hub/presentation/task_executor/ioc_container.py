# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from typing import Protocol

from dishka import (
    Provider,
    Scope,
    AsyncContainer,
    make_async_container,
)
from dishka.integrations.taskiq import TaskiqProvider

from connection_hub.domain import (
    DisconnectFromLobby,
    TryToDisqualifyPlayer,
)
from connection_hub.application import (
    LobbyGateway,
    GameGateway,
    EventPublisher,
    TaskScheduler,
    CentrifugoClient,
    TransactionManager,
    TryToDisconnectFromLobbyProcessor,
    TryToDisqualifyPlayerProcessor,
)
from connection_hub.infrastructure import (
    httpx_client_factory,
    CentrifugoConfig,
    load_centrifugo_config,
    HTTPXCentrifugoClient,
    redis_factory,
    redis_pipeline_factory,
    LobbyMapperConfig,
    load_lobby_mapper_config,
    LobbyMapper,
    GameMapperConfig,
    load_game_mapper_config,
    GameMapper,
    LockManagerConfig,
    load_lock_manager_config,
    lock_manager_factory,
    RedisTransactionManager,
    NATSConfig,
    load_nats_config,
    nats_client_factory,
    nats_jetstream_factory,
    NATSEventPublisher,
    taskiq_redis_schedule_source_factory,
    TaskiqTaskScheduler,
    RedisConfig,
    load_redis_config,
    common_retort_factory,
    get_operation_id,
)


class _ConfigFactory[C](Protocol):
    def __call__(self) -> C:
        raise NotImplementedError


def ioc_container_factory(
    *,
    centrifugo_config_factory: _ConfigFactory[CentrifugoConfig] = (
        load_centrifugo_config
    ),
    redis_config_factory: _ConfigFactory[RedisConfig] = load_redis_config,
    lobby_mapper_config_factory: _ConfigFactory[LobbyMapperConfig] = (
        load_lobby_mapper_config
    ),
    game_mapper_config_factory: _ConfigFactory[GameMapperConfig] = (
        load_game_mapper_config
    ),
    lock_manager_config_factory: _ConfigFactory[LockManagerConfig] = (
        load_lock_manager_config
    ),
    nats_config_factory: _ConfigFactory[NATSConfig] = load_nats_config,
) -> AsyncContainer:
    provider = Provider()

    context = {
        CentrifugoConfig: centrifugo_config_factory(),
        RedisConfig: redis_config_factory(),
        LobbyMapperConfig: lobby_mapper_config_factory(),
        GameMapperConfig: game_mapper_config_factory(),
        LockManagerConfig: lock_manager_config_factory(),
        NATSConfig: nats_config_factory(),
    }

    provider.from_context(CentrifugoConfig, scope=Scope.APP)
    provider.from_context(RedisConfig, scope=Scope.APP)
    provider.from_context(LobbyMapperConfig, scope=Scope.APP)
    provider.from_context(GameMapperConfig, scope=Scope.APP)
    provider.from_context(LockManagerConfig, scope=Scope.APP)
    provider.from_context(NATSConfig, scope=Scope.APP)

    provider.provide(get_operation_id, scope=Scope.REQUEST)
    provider.provide(common_retort_factory, scope=Scope.APP)

    provider.provide(httpx_client_factory, scope=Scope.APP)
    provider.provide(redis_factory, scope=Scope.APP)
    provider.provide(redis_pipeline_factory, scope=Scope.REQUEST)
    provider.provide(nats_client_factory, scope=Scope.APP)
    provider.provide(nats_jetstream_factory, scope=Scope.APP)
    provider.provide(taskiq_redis_schedule_source_factory, scope=Scope.APP)

    provider.provide(lock_manager_factory, scope=Scope.REQUEST)
    provider.provide(LobbyMapper, provides=LobbyGateway, scope=Scope.REQUEST)
    provider.provide(GameMapper, provides=GameGateway, scope=Scope.REQUEST)
    provider.provide(
        RedisTransactionManager,
        provides=TransactionManager,
        scope=Scope.REQUEST,
    )

    provider.provide(
        NATSEventPublisher,
        scope=Scope.REQUEST,
        provides=EventPublisher,
    )
    provider.provide(
        HTTPXCentrifugoClient,
        scope=Scope.REQUEST,
        provides=CentrifugoClient,
    )
    provider.provide(
        TaskiqTaskScheduler,
        scope=Scope.REQUEST,
        provides=TaskScheduler,
    )

    provider.provide(DisconnectFromLobby, scope=Scope.APP)
    provider.provide(TryToDisqualifyPlayer, scope=Scope.APP)

    provider.provide(TryToDisconnectFromLobbyProcessor, scope=Scope.REQUEST)
    provider.provide(TryToDisqualifyPlayerProcessor, scope=Scope.REQUEST)

    return make_async_container(provider, TaskiqProvider(), context=context)
