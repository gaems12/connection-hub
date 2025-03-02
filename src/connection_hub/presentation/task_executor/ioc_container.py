# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from dishka import (
    Provider,
    Scope,
    AsyncContainer,
    make_async_container,
)

from connection_hub.domain import TryToDisqualifyPlayer
from connection_hub.application import (
    GameGateway,
    EventPublisher,
    TaskScheduler,
    TransactionManager,
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
    RealEventPublisher,
    default_operation_id_factory,
)
from .context_var_setter import ContextVarSetter


def ioc_container_factory() -> AsyncContainer:
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

    provider.provide(default_operation_id_factory, scope=Scope.REQUEST)
    provider.provide(ContextVarSetter, scope=Scope.REQUEST)
    provider.provide(common_retort_factory, scope=Scope.APP)

    provider.provide(httpx_client_factory, scope=Scope.APP)
    provider.provide(redis_factory, scope=Scope.APP)
    provider.provide(redis_pipeline_factory, scope=Scope.REQUEST)
    provider.provide(nats_client_factory, scope=Scope.APP)
    provider.provide(nats_jetstream_factory, scope=Scope.APP)
    provider.provide(taskiq_redis_schedule_source_factory, scope=Scope.APP)

    provider.provide(lock_manager_factory, scope=Scope.REQUEST)
    provider.provide(GameMapper, provides=GameGateway, scope=Scope.REQUEST)
    provider.provide(
        RedisTransactionManager,
        provides=TransactionManager,
        scope=Scope.REQUEST,
    )

    provider.provide(NATSEventPublisher, scope=Scope.REQUEST)
    provider.provide(HTTPXCentrifugoClient, scope=Scope.REQUEST)
    provider.provide(
        RealEventPublisher,
        provides=EventPublisher,
        scope=Scope.REQUEST,
    )

    provider.provide(
        TaskiqTaskScheduler,
        scope=Scope.REQUEST,
        provides=TaskScheduler,
    )

    provider.provide(TryToDisqualifyPlayer, scope=Scope.APP)
    provider.provide(TryToDisqualifyPlayerProcessor, scope=Scope.REQUEST)

    return make_async_container(provider, context=context)
