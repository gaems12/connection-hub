# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from unittest.mock import AsyncMock
from datetime import timedelta
from typing import Final

from uuid_extensions import uuid7

from connection_hub.domain import (
    UserRole,
    LobbyId,
    UserId,
    ConnectFourLobby,
    DisconnectFromLobby,
)
from connection_hub.application import (
    UserDisconnectedFromLobbyEvent,
    TryToDisconnectFromLobbyCommand,
    TryToDisconnectFromLobbyProcessor,
)
from .fakes import (
    FakeLobbyGateway,
    FakeEventPublisher,
    FakeCentrifugoClient,
)


_FIRST_USER_ID: Final = UserId(uuid7())
_SECOND_USER_ID: Final = UserId(uuid7())

_LOBBY_ID: Final = LobbyId(uuid7())
_NAME: Final = "Connect Four for money!!"
_PASSWORD: Final = "12345"
_TIME_FOR_EACH_PLAYER: Final = timedelta(minutes=1)


async def test_try_to_disconnect_from_lobby():
    lobby = ConnectFourLobby(
        id=_LOBBY_ID,
        name=_NAME,
        users={
            _FIRST_USER_ID: UserRole.ADMIN,
            _SECOND_USER_ID: UserRole.REGULAR_MEMBER,
        },
        admin_role_transfer_queue=[_SECOND_USER_ID],
        password=_PASSWORD,
        time_for_each_player=_TIME_FOR_EACH_PLAYER,
    )

    lobby_gateway = FakeLobbyGateway({lobby.id: lobby})
    event_publisher = FakeEventPublisher()
    centrifugo_client = FakeCentrifugoClient()

    command = TryToDisconnectFromLobbyCommand(
        lobby_id=_LOBBY_ID,
        user_id=_FIRST_USER_ID,
    )
    command_processor = TryToDisconnectFromLobbyProcessor(
        disconnect_from_lobby=DisconnectFromLobby(),
        lobby_gateway=lobby_gateway,
        event_publisher=event_publisher,
        centrifugo_client=centrifugo_client,
        transaction_manager=AsyncMock(),
    )

    await command_processor.process(command)

    expected_lobby = lobby = ConnectFourLobby(
        id=_LOBBY_ID,
        name=_NAME,
        users={_SECOND_USER_ID: UserRole.ADMIN},
        admin_role_transfer_queue=[],
        password=_PASSWORD,
        time_for_each_player=_TIME_FOR_EACH_PLAYER,
    )
    assert expected_lobby == lobby

    expected_event = UserDisconnectedFromLobbyEvent(
        lobby_id=_LOBBY_ID,
        user_id=_FIRST_USER_ID,
        new_admin_id=_SECOND_USER_ID,
    )
    assert expected_event in event_publisher.events

    expected_centrifugo_publication = {
        "type": "user_disconnected",
        "user_id": _FIRST_USER_ID.hex,
        "new_admin_id": _SECOND_USER_ID.hex,
    }
    assert (
        centrifugo_client.publications[f"lobbies:{_LOBBY_ID.hex}"]
        == expected_centrifugo_publication
    )

    assert (
        f"lobbies:{_LOBBY_ID.hex}"
        not in centrifugo_client.subscriptions[_FIRST_USER_ID.hex]
    )
