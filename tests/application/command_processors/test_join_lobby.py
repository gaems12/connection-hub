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
    JoinLobby,
)
from connection_hub.application import (
    UserJoinedLobbyEvent,
    JoinLobbyCommand,
    JoinLobbyProcessor,
)
from .fakes import (
    FakeLobbyGateway,
    FakeGameGateway,
    FakeEventPublisher,
    FakeCentrifugoClient,
    FakeIdentityProvider,
)


_ADMIN_ID: Final = UserId(uuid7())
_CURRENT_USER_ID: Final = UserId(uuid7())

_LOBBY_ID: Final = LobbyId(uuid7())
_NAME: Final = "Connect Four for money!!"
_PASSWORD: Final = "12345"
_TIME_FOR_EACH_PLAYER: Final = timedelta(minutes=1)


async def test_join_lobby_processor():
    lobby = ConnectFourLobby(
        id=_LOBBY_ID,
        name=_NAME,
        users={_ADMIN_ID: UserRole.ADMIN},
        admin_role_transfer_queue=[],
        password=_PASSWORD,
        time_for_each_player=_TIME_FOR_EACH_PLAYER,
    )

    lobby_gateway = FakeLobbyGateway({lobby.id: lobby})
    event_publisher = FakeEventPublisher([])
    centrifugo_client = FakeCentrifugoClient({})
    identity_provider = FakeIdentityProvider(_CURRENT_USER_ID)

    command = JoinLobbyCommand(
        lobby_id=_LOBBY_ID,
        password=_PASSWORD,
    )
    command_processor = JoinLobbyProcessor(
        join_lobby=JoinLobby(),
        lobby_gateway=lobby_gateway,
        game_gateway=FakeGameGateway({}),
        event_publisher=event_publisher,
        centrifugo_client=centrifugo_client,
        transaction_manager=AsyncMock(),
        identity_provider=identity_provider,
    )

    await command_processor.process(command)

    expected_lobby = ConnectFourLobby(
        id=_LOBBY_ID,
        name=_NAME,
        users={
            _ADMIN_ID: UserRole.ADMIN,
            _CURRENT_USER_ID: UserRole.REGULAR_MEMBER,
        },
        admin_role_transfer_queue=[_CURRENT_USER_ID],
        password=_PASSWORD,
        time_for_each_player=_TIME_FOR_EACH_PLAYER,
    )
    assert expected_lobby == lobby

    expected_event = UserJoinedLobbyEvent(
        lobby_id=_LOBBY_ID,
        user_id=_CURRENT_USER_ID,
    )
    assert expected_event in event_publisher.events

    expected_centrifugo_publication = {
        "type": "user_joined",
        "user_id": _CURRENT_USER_ID.hex,
    }
    assert (
        centrifugo_client.publications[f"lobbies:{_LOBBY_ID.hex}"]
        == expected_centrifugo_publication
    )
