# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from dishka import (
    Provider,
    Scope,
    AsyncContainer,
    make_async_container,
)
from dishka.integrations.faststream import FastStreamProvider

from connection_hub.domain import (
    CreateLobby,
    JoinLobby,
    RemoveFromLobby,
    KickFromLobby,
    CreateGame,
    ReconnectToGame,
)
from connection_hub.application import (
    LobbyGateway,
    GameGateway,
    EventPublisher,
    TaskScheduler,
    CentrifugoClient,
    TransactionManager,
    IdentityProvider,
    CreateLobbyProcessor,
    JoinLobbyProcessor,
    LeaveLobbyProcessor,
    KickFromLobbyProcessor,
    CreateGameProcessor,
    AcknowledgePresenceProcessor,
    ReconnectToGameProcessor,
    EndGameProcessor,
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
from .identity_provider import MessageBrokerIdentityProvider


def ioc_container_factory(context: dict | None = None) -> AsyncContainer:
    provider = Provider()

    context = context or {
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
    provider.provide(LobbyMapper, scope=Scope.REQUEST, provides=LobbyGateway)
    provider.provide(GameMapper, scope=Scope.REQUEST, provides=GameGateway)
    provider.provide(
        RedisTransactionManager,
        scope=Scope.REQUEST,
        provides=TransactionManager,
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
    provider.provide(
        MessageBrokerIdentityProvider,
        scope=Scope.REQUEST,
        provides=IdentityProvider,
    )

    provider.provide(CreateLobby, scope=Scope.APP)
    provider.provide(JoinLobby, scope=Scope.APP)
    provider.provide(RemoveFromLobby, scope=Scope.APP)
    provider.provide(KickFromLobby, scope=Scope.APP)
    provider.provide(CreateGame, scope=Scope.APP)
    provider.provide(ReconnectToGame, scope=Scope.APP)

    provider.provide(CreateLobbyProcessor, scope=Scope.REQUEST)
    provider.provide(JoinLobbyProcessor, scope=Scope.REQUEST)
    provider.provide(LeaveLobbyProcessor, scope=Scope.REQUEST)
    provider.provide(KickFromLobbyProcessor, scope=Scope.REQUEST)
    provider.provide(CreateGameProcessor, scope=Scope.REQUEST)
    provider.provide(AcknowledgePresenceProcessor, scope=Scope.REQUEST)
    provider.provide(ReconnectToGameProcessor, scope=Scope.REQUEST)
    provider.provide(EndGameProcessor, scope=Scope.REQUEST)

    return make_async_container(
        provider,
        FastStreamProvider(),
        context=context,
    )
