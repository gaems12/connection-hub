# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from unittest.mock import AsyncMock
from datetime import timedelta
from typing import Final

from uuid_extensions import uuid7

from connection_hub.domain import (
    UserRole,
    PlayerStatus,
    LobbyId,
    UserId,
    PlayerState,
    ConnectFourLobby,
    ConnectFourGame,
    CreateGame,
)
from connection_hub.application import (
    ConnectFourGameCreatedEvent,
    CreateGameProcessor,
)
from .fakes import (
    ANY_PLAYER_STATE_ID,
    ANY_GAME_ID,
    ANY_DATETIME,
    FakeLobbyGateway,
    FakeGameGateway,
    FakeEventPublisher,
    FakeIdentityProvider,
)


_CURRENT_USER_ID: Final = UserId(uuid7())
_OTHER_USER_ID: Final = UserId(uuid7())

_LOBBY_ID: Final = LobbyId(uuid7())
_NAME: Final = "Connect Four for money!!"
_PASSWORD: Final = "12345"
_TIME_FOR_EACH_PLAYER: Final = timedelta(minutes=1)


async def test_create_game_processor():
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
    game_gateway = FakeGameGateway()
    event_publisher = FakeEventPublisher()

    processor = CreateGameProcessor(
        create_game=CreateGame(),
        lobby_gateway=lobby_gateway,
        game_gateway=game_gateway,
        event_publisher=event_publisher,
        transaction_manager=AsyncMock(),
        identity_provider=FakeIdentityProvider(_CURRENT_USER_ID),
    )

    await processor.process()

    expected_game = ConnectFourGame(
        id=ANY_GAME_ID,
        players={
            _CURRENT_USER_ID: PlayerState(
                id=ANY_PLAYER_STATE_ID,
                status=PlayerStatus.CONNECTED,
                time_left=timedelta(seconds=40),
            ),
            _OTHER_USER_ID: PlayerState(
                id=ANY_PLAYER_STATE_ID,
                status=PlayerStatus.CONNECTED,
                time_left=timedelta(seconds=40),
            ),
        },
        created_at=ANY_DATETIME,
        time_for_each_player=_TIME_FOR_EACH_PLAYER,
    )
    assert expected_game in game_gateway.games

    expected_event = ConnectFourGameCreatedEvent(
        game_id=ANY_GAME_ID,
        lobby_id=_LOBBY_ID,
        first_player_id=_CURRENT_USER_ID,
        second_player_id=_OTHER_USER_ID,
        time_for_each_player=_TIME_FOR_EACH_PLAYER,
        created_at=ANY_DATETIME,
    )
    assert expected_event in event_publisher.events
