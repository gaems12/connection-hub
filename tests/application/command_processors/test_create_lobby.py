# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from unittest.mock import AsyncMock
from datetime import timedelta
from typing import Final

from uuid_extensions import uuid7

from connection_hub.domain import (
    UserRole,
    UserId,
    ConnectFourRuleSet,
    ConnectFourLobby,
    CreateLobby,
)
from connection_hub.application import (
    LobbyCreatedEvent,
    CreateLobbyCommand,
    CreateLobbyProcessor,
)
from .fakes import (
    ANY_LOBBY_ID,
    ANY_STR,
    FakeLobbyGateway,
    FakeGameGateway,
    FakeEventPublisher,
    FakeCentrifugoClient,
    FakeIdentityProvider,
)


_USER_ID: Final = UserId(uuid7())
_NAME: Final = "Connect Four for money!!"
_PASSWORD: Final = "12345"

_CONNECT_FOUR_RULE_SET: Final = ConnectFourRuleSet(
    time_for_each_player=timedelta(minutes=3),
)


async def test_create_lobby_processor():
    lobby_gateway = FakeLobbyGateway()
    event_publisher = FakeEventPublisher()
    centrifugo_client = FakeCentrifugoClient()

    command = CreateLobbyCommand(
        name=_NAME,
        rule_set=_CONNECT_FOUR_RULE_SET,
        password=_PASSWORD,
    )
    command_processor = CreateLobbyProcessor(
        create_lobby=CreateLobby(),
        lobby_gateway=lobby_gateway,
        game_gateway=FakeGameGateway({}),
        event_publisher=event_publisher,
        centrifugo_client=centrifugo_client,
        transaction_manager=AsyncMock(),
        identity_provider=FakeIdentityProvider(_USER_ID),
    )

    await command_processor.process(command)

    expected_lobby = ConnectFourLobby(
        id=ANY_LOBBY_ID,
        name=_NAME,
        users={_USER_ID: UserRole.ADMIN},
        admin_role_transfer_queue=[],
        password=_PASSWORD,
        time_for_each_player=_CONNECT_FOUR_RULE_SET.time_for_each_player,
    )
    assert expected_lobby in lobby_gateway.lobbies

    expected_event = LobbyCreatedEvent(
        lobby_id=ANY_LOBBY_ID,
        name=_NAME,
        admin_id=_USER_ID,
        has_password=True,
        rule_set=_CONNECT_FOUR_RULE_SET,
    )
    assert expected_event in event_publisher.events

    expected_centrifugo_publication = {
        "type": "lobby_created",
        "lobby_id": ANY_STR,
        "name": _NAME,
        "rule_set": {
            "type": "connect_four",
            "time_for_each_player": (
                _CONNECT_FOUR_RULE_SET.time_for_each_player.total_seconds()
            ),
        },
    }
    assert (
        centrifugo_client.publications[f"#{_USER_ID.hex}"]
        == expected_centrifugo_publication
    )
