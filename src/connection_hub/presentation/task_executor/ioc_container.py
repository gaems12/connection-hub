# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from dishka import (
    Provider,
    Scope,
    AsyncContainer,
    make_async_container,
)
from dishka.integrations.taskiq import TaskiqProvider

from connection_hub.domain import (
    RemoveFromLobby,
    DisconnectFromGame,
    TryToDisqualifyPlayer,
)
from connection_hub.application import (
    LobbyGateway,
    GameGateway,
    EventPublisher,
    TaskScheduler,
    CentrifugoClient,
    TransactionManager,
    RemoveFromLobbyProcessor,
    DisconnectFromGameProcessor,
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


def ioc_container_factory(context: dict | None = None) -> AsyncContainer:
    provider = Provider()

    context = {
        CentrifugoConfig: load_centrifugo_config(),
        RedisConfig: load_redis_config(),
        LobbyMapperConfig: load_lobby_mapper_config(),
        GameMapperConfig: load_game_mapper_config(),
        LockManagerConfig: load_lock_manager_config(),
        NATSConfig: load_nats_config(),
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

    provider.provide(RemoveFromLobby, scope=Scope.APP)
    provider.provide(DisconnectFromGame, scope=Scope.APP)
    provider.provide(TryToDisqualifyPlayer, scope=Scope.APP)

    provider.provide(RemoveFromLobbyProcessor, scope=Scope.REQUEST)
    provider.provide(DisconnectFromGameProcessor, scope=Scope.REQUEST)
    provider.provide(TryToDisqualifyPlayerProcessor, scope=Scope.REQUEST)

    return make_async_container(provider, TaskiqProvider(), context=context)
