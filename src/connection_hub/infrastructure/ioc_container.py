# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

__all__ = ("ioc_container_factory",)

from typing import Any, Callable, Coroutine, Iterable

from dishka import Provider, Scope, AsyncContainer, make_async_container

from connection_hub.domain import (
    CreateLobby,
    JoinLobby,
    LeaveLobby,
    CreateGame,
    DisconnectFromGame,
)
from connection_hub.application import (
    LobbyGateway,
    GameGateway,
    EventPublisher,
    TaskScheduler,
    TransactionManager,
    IdentityProvider,
    CreateLobbyCommand,
    CreateLobbyProcessor,
    JoinLobbyCommand,
    JoinLobbyProcessor,
    LeaveLobbyProcessor,
    CreateGameProcessor,
    DisconnectFromGameProcessor,
    DisqualifyPlayerProcessor,
)
from .clients import (
    httpx_client_factory,
    CentrifugoConfig,
    load_centrifugo_config,
    HTTPXCentrifugoClient,
)
from .database import (
    redis_factory,
    redis_pipeline_factory,
    LobbyMapperConfig,
    lobby_mapper_config_from_env,
    LobbyMapper,
    GameMapperConfig,
    game_mapper_config_from_env,
    GameMapper,
    LockManagerConfig,
    lock_manager_config_from_env,
    lock_manager_factory,
    RedisTransactionManager,
)
from .message_broker import (
    NATSConfig,
    nats_config_from_env,
    nats_client_factory,
    nats_jetstream_factory,
    NATSEventPublisher,
)
from .scheduling import (
    taskiq_redis_schedule_source_factory,
    TaskiqTaskScheduler,
)
from .redis_config import RedisConfig, load_redis_config
from .common_retort import common_retort_factory
from .event_publisher import RealEventPublisher
from .identity_provider import HTTPIdentityProvider


type _Command = CreateLobbyCommand | JoinLobbyCommand

type _CommandFactory = Callable[..., Coroutine[Any, Any, _Command]]


def ioc_container_factory(
    command_factories: Iterable[_CommandFactory],
    *extra_providers: Provider,
) -> AsyncContainer:
    provider = Provider()

    context = {
        CentrifugoConfig: load_centrifugo_config(),
        RedisConfig: load_redis_config(),
        LobbyMapperConfig: lobby_mapper_config_from_env(),
        GameMapperConfig: game_mapper_config_from_env(),
        LockManagerConfig: lock_manager_config_from_env(),
        NATSConfig: nats_config_from_env(),
    }

    provider.from_context(CentrifugoConfig, scope=Scope.APP)
    provider.from_context(RedisConfig, scope=Scope.APP)
    provider.from_context(LobbyMapperConfig, scope=Scope.APP)
    provider.from_context(GameMapperConfig, scope=Scope.APP)
    provider.from_context(LockManagerConfig, scope=Scope.APP)
    provider.from_context(NATSConfig, scope=Scope.APP)

    provider.provide(httpx_client_factory, scope=Scope.APP)
    provider.provide(redis_factory, scope=Scope.APP)
    provider.provide(redis_pipeline_factory, scope=Scope.REQUEST)
    provider.provide(nats_client_factory, scope=Scope.APP)
    provider.provide(nats_jetstream_factory, scope=Scope.APP)
    provider.provide(taskiq_redis_schedule_source_factory, scope=Scope.APP)

    provider.provide(common_retort_factory, scope=Scope.APP)

    provider.provide(lock_manager_factory, scope=Scope.REQUEST)
    provider.provide(LobbyMapper, provides=LobbyGateway, scope=Scope.REQUEST)
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

    provider.provide(
        HTTPIdentityProvider,
        scope=Scope.REQUEST,
        provides=IdentityProvider,
    )

    provider.provide(CreateLobby, scope=Scope.APP)
    provider.provide(JoinLobby, scope=Scope.APP)
    provider.provide(LeaveLobby, scope=Scope.APP)
    provider.provide(CreateGame, scope=Scope.APP)
    provider.provide(DisconnectFromGame, scope=Scope.APP)

    for command_factory in command_factories:
        provider.provide(command_factory, scope=Scope.REQUEST)

    provider.provide(CreateLobbyProcessor, scope=Scope.REQUEST)
    provider.provide(JoinLobbyProcessor, scope=Scope.REQUEST)
    provider.provide(LeaveLobbyProcessor, scope=Scope.REQUEST)
    provider.provide(CreateGameProcessor, scope=Scope.REQUEST)
    provider.provide(DisconnectFromGameProcessor, scope=Scope.REQUEST)
    provider.provide(DisqualifyPlayerProcessor, scope=Scope.REQUEST)

    return make_async_container(provider, *extra_providers, context=context)
