# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from unittest.mock import AsyncMock

import pytest
from faststream import FastStream
from faststream.nats import NatsBroker, TestNatsBroker, TestApp
from dishka import Provider, Scope, AsyncContainer, make_async_container
from dishka.integrations.faststream import FastStreamProvider
from uuid_extensions import uuid7

from connection_hub.application import (
    CreateLobbyProcessor,
    JoinLobbyProcessor,
    LeaveLobbyProcessor,
    KickFromLobbyProcessor,
    CreateGameProcessor,
    DisconnectFromGameProcessor,
    ReconnectToGameProcessor,
    TryToDisqualifyPlayerProcessor,
    EndGameProcessor,
)
from connection_hub.infrastructure import NATSConfig
from connection_hub.presentation.message_consumer import (
    create_lobby,
    join_lobby,
    leave_lobby,
    kick_from_lobby,
    create_game,
    end_game,
    disconnect_from_game,
    reconnect_to_game,
    create_broker,
)
from connection_hub.main.message_consumer import create_message_consumer_app


@pytest.fixture(scope="function")
def broker(nats_config: NATSConfig) -> NatsBroker:
    return create_broker(nats_config.url)


@pytest.fixture(scope="function")
def ioc_container() -> AsyncContainer:
    provider = Provider()

    provider.provide(
        lambda: AsyncMock(),
        scope=Scope.REQUEST,
        provides=CreateLobbyProcessor,
    )
    provider.provide(
        lambda: AsyncMock(),
        scope=Scope.REQUEST,
        provides=JoinLobbyProcessor,
    )
    provider.provide(
        lambda: AsyncMock(),
        scope=Scope.REQUEST,
        provides=LeaveLobbyProcessor,
    )
    provider.provide(
        lambda: AsyncMock(),
        scope=Scope.REQUEST,
        provides=KickFromLobbyProcessor,
    )
    provider.provide(
        lambda: AsyncMock(),
        scope=Scope.REQUEST,
        provides=CreateGameProcessor,
    )
    provider.provide(
        lambda: AsyncMock(),
        scope=Scope.REQUEST,
        provides=DisconnectFromGameProcessor,
    )
    provider.provide(
        lambda: AsyncMock(),
        scope=Scope.REQUEST,
        provides=ReconnectToGameProcessor,
    )
    provider.provide(
        lambda: AsyncMock(),
        scope=Scope.REQUEST,
        provides=TryToDisqualifyPlayerProcessor,
    )
    provider.provide(
        lambda: AsyncMock(),
        scope=Scope.REQUEST,
        provides=EndGameProcessor,
    )

    return make_async_container(provider, FastStreamProvider())


@pytest.fixture(scope="function")
def app(broker: NatsBroker, ioc_container: AsyncContainer) -> FastStream:
    app = create_message_consumer_app(
        broker=broker,
        ioc_container=ioc_container,
    )
    return app


async def test_create_lobby(app: FastStream, broker: NatsBroker):
    async with (
        TestApp(app),
        TestNatsBroker(broker, with_real=True) as test_broker,
    ):
        message = {
            "user_id": uuid7().hex,
            "name": "Connect Four Game For Money!!!",
            "rule_set": {
                "type": "connect_four",
                "time_for_each_player": 60,
            },
            "password": "qwerty12345",
        }
        await test_broker.publish(
            message=message,
            subject="api_gateway.lobby.created",
            stream="games",
        )
        await create_lobby.wait_call(1)


async def test_join_lobby(app: FastStream, broker: NatsBroker):
    async with (
        TestApp(app),
        TestNatsBroker(broker, with_real=True) as test_broker,
    ):
        message = {
            "user_id": uuid7().hex,
            "lobby_id": uuid7().hex,
            "password": "qwerty12345",
        }
        await test_broker.publish(
            message=message,
            subject="api_gateway.lobby.user_joined",
            stream="games",
        )
        await join_lobby.wait_call(1)


async def test_leave_lobby(app: FastStream, broker: NatsBroker):
    async with (
        TestApp(app),
        TestNatsBroker(broker, with_real=True) as test_broker,
    ):
        await test_broker.publish(
            message={"user_id": uuid7().hex, "lobby_id": uuid7().hex},
            subject="api_gateway.lobby.user_left",
            stream="games",
        )
        await leave_lobby.wait_call(1)


async def test_kick_from_lobby(app: FastStream, broker: NatsBroker):
    async with (
        TestApp(app),
        TestNatsBroker(broker, with_real=True) as test_broker,
    ):
        await test_broker.publish(
            message={"lobby_id": uuid7().hex, "user_id": uuid7().hex},
            subject="api_gateway.lobby.user_kicked",
            stream="games",
        )
        await kick_from_lobby.wait_call(1)


async def test_create_game(app: FastStream, broker: NatsBroker):
    async with (
        TestApp(app),
        TestNatsBroker(broker, with_real=True) as test_broker,
    ):
        await test_broker.publish(
            message={"user_id": uuid7().hex, "lobby_id": uuid7().hex},
            subject="api_gateway.game.created",
            stream="games",
        )
        await create_game.wait_call(1)


async def test_end_game(app: FastStream, broker: NatsBroker):
    async with (
        TestApp(app),
        TestNatsBroker(broker, with_real=True) as test_broker,
    ):
        await test_broker.publish(
            message={"game_id": uuid7().hex},
            subject="connect_four.game.ended",
            stream="games",
        )
        await end_game.wait_call(1)


async def test_disconnect_from_game(app: FastStream, broker: NatsBroker):
    async with (
        TestApp(app),
        TestNatsBroker(broker, with_real=True) as test_broker,
    ):
        await test_broker.publish(
            message={"user_id": uuid7().hex},
            subject="api_gateway.game.player_disconnected",
            stream="games",
        )
        await disconnect_from_game.wait_call(1)


async def test_reconnect_to_game(app: FastStream, broker: NatsBroker):
    async with (
        TestApp(app),
        TestNatsBroker(broker, with_real=True) as test_broker,
    ):
        await test_broker.publish(
            message={"user_id": uuid7().hex, "game_id": uuid7().hex},
            subject="api_gateway.game.player_reconnected",
            stream="games",
        )
        await reconnect_to_game.wait_call(1)
