# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from unittest.mock import AsyncMock
from datetime import timedelta
from typing import Final

import pytest
from uuid_extensions import uuid7

from connection_hub.domain import (
    UserRole,
    LobbyId,
    UserId,
    ConnectFourLobby,
    LeaveLobby,
)
from connection_hub.application import (
    UserLeftLobbyEvent,
    LeaveLobbyProcessor,
    CurrentUserNotInLobbyError,
)
from .fakes import (
    FakeLobbyGateway,
    FakeEventPublisher,
    FakeCentrifugoClient,
    FakeIdentityProvider,
)


_CURRENT_USER_ID: Final = UserId(uuid7())
_OTHER_USER_ID: Final = UserId(uuid7())

_LOBBY_ID: Final = LobbyId(uuid7())
_NAME: Final = "Connect Four for money!!"
_PASSWORD: Final = "12345"
_TIME_FOR_EACH_PLAYER: Final = timedelta(minutes=1)


async def test_leave_lobby_processor():
    lobby = ConnectFourLobby(
        id=_LOBBY_ID,
        name=_NAME,
        users={
            _CURRENT_USER_ID: UserRole.ADMIN,
            _OTHER_USER_ID: UserRole.REGULAR_MEMBER,
        },
        admin_role_transfer_queue=[_OTHER_USER_ID],
        password=_PASSWORD,
        time_for_each_player=_TIME_FOR_EACH_PLAYER,
    )

    lobby_gateway = FakeLobbyGateway({lobby.id: lobby})
    event_publisher = FakeEventPublisher()
    centrifugo_client = FakeCentrifugoClient(
        subscriptons={_CURRENT_USER_ID.hex: [f"lobbies:{_LOBBY_ID.hex}"]},
    )

    processor = LeaveLobbyProcessor(
        leave_lobby=LeaveLobby(),
        lobby_gateway=lobby_gateway,
        event_publisher=event_publisher,
        centrifugo_client=centrifugo_client,
        transaction_manager=AsyncMock(),
        identity_provider=FakeIdentityProvider(_CURRENT_USER_ID),
    )

    await processor.process()

    expected_lobby = lobby = ConnectFourLobby(
        id=_LOBBY_ID,
        name=_NAME,
        users={_OTHER_USER_ID: UserRole.ADMIN},
        admin_role_transfer_queue=[],
        password=_PASSWORD,
        time_for_each_player=_TIME_FOR_EACH_PLAYER,
    )
    assert expected_lobby == lobby

    expected_event = UserLeftLobbyEvent(
        lobby_id=_LOBBY_ID,
        user_id=_CURRENT_USER_ID,
        new_admin_id=_OTHER_USER_ID,
    )
    assert expected_event in event_publisher.events

    expected_centrifugo_publication = {
        "type": "user_left",
        "user_id": _CURRENT_USER_ID.hex,
        "new_admin_id": _OTHER_USER_ID.hex,
    }
    assert (
        centrifugo_client.publications[f"lobbies:{_LOBBY_ID.hex}"]
        == expected_centrifugo_publication
    )

    assert (
        f"lobbies:{_LOBBY_ID.hex}"
        not in centrifugo_client.subscriptions[_CURRENT_USER_ID.hex]
    )


async def test_leave_lobby_processor_errors():
    event_publisher = FakeEventPublisher()
    centrifugo_client = FakeCentrifugoClient()

    command_processor = LeaveLobbyProcessor(
        leave_lobby=LeaveLobby(),
        lobby_gateway=FakeLobbyGateway(),
        event_publisher=event_publisher,
        centrifugo_client=centrifugo_client,
        transaction_manager=AsyncMock(),
        identity_provider=FakeIdentityProvider(_CURRENT_USER_ID),
    )

    with pytest.raises(CurrentUserNotInLobbyError):
        await command_processor.process()

    assert not event_publisher.events
    assert not centrifugo_client.publications
