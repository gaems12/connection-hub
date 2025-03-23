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
    PlayerStatus,
    LobbyId,
    UserId,
    PlayerState,
    ConnectFourLobby,
    Lobby,
    ConnectFourGame,
    CreateGame,
    UserIsNotAdminError,
)
from connection_hub.application import (
    ConnectFourGameCreatedEvent,
    DisconnectFromGameTask,
    CreateGameCommand,
    CreateGameProcessor,
    LobbyDoesNotExistError,
    CurrentUserNotInLobbyError,
)
from .fakes import (
    ANY_PLAYER_STATE_ID,
    ANY_GAME_ID,
    ANY_DATETIME,
    ANY_STR,
    FakeLobbyGateway,
    FakeGameGateway,
    FakeEventPublisher,
    FakeTaskScheduler,
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
    task_scheduler = FakeTaskScheduler()

    command = CreateGameCommand(lobby_id=_LOBBY_ID)
    command_processor = CreateGameProcessor(
        create_game=CreateGame(),
        lobby_gateway=lobby_gateway,
        game_gateway=game_gateway,
        event_publisher=event_publisher,
        task_scheduler=task_scheduler,
        transaction_manager=AsyncMock(),
        identity_provider=FakeIdentityProvider(_CURRENT_USER_ID),
    )

    await command_processor.process(command)

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

    first_expected_task = DisconnectFromGameTask(
        id=ANY_STR,
        execute_at=ANY_DATETIME,
        game_id=ANY_GAME_ID,
        player_id=_CURRENT_USER_ID,
    )
    assert first_expected_task in task_scheduler.tasks

    first_expected_task = DisconnectFromGameTask(
        id=ANY_STR,
        execute_at=ANY_DATETIME,
        game_id=ANY_GAME_ID,
        player_id=_OTHER_USER_ID,
    )
    assert first_expected_task in task_scheduler.tasks

    expected_event = ConnectFourGameCreatedEvent(
        game_id=ANY_GAME_ID,
        lobby_id=_LOBBY_ID,
        first_player_id=_CURRENT_USER_ID,
        second_player_id=_OTHER_USER_ID,
        time_for_each_player=_TIME_FOR_EACH_PLAYER,
        created_at=ANY_DATETIME,
    )
    assert expected_event in event_publisher.events


@pytest.mark.parametrize(
    ["lobby", "command", "expected_error"],
    [
        [
            None,
            CreateGameCommand(lobby_id=_LOBBY_ID),
            LobbyDoesNotExistError,
        ],
        [
            ConnectFourLobby(
                id=_LOBBY_ID,
                name=_NAME,
                users={_OTHER_USER_ID: UserRole.ADMIN},
                admin_role_transfer_queue=[],
                password=_PASSWORD,
                time_for_each_player=_TIME_FOR_EACH_PLAYER,
            ),
            CreateGameCommand(lobby_id=_LOBBY_ID),
            CurrentUserNotInLobbyError,
        ],
        [
            ConnectFourLobby(
                id=_LOBBY_ID,
                name=_NAME,
                users={
                    _OTHER_USER_ID: UserRole.ADMIN,
                    _CURRENT_USER_ID: UserRole.REGULAR_MEMBER,
                },
                admin_role_transfer_queue=[_CURRENT_USER_ID],
                password=_PASSWORD,
                time_for_each_player=_TIME_FOR_EACH_PLAYER,
            ),
            CreateGameCommand(lobby_id=_LOBBY_ID),
            UserIsNotAdminError,
        ],
    ],
)
async def test_create_game_processor_errors(
    lobby: Lobby | None,
    command: CreateGameCommand,
    expected_error: Exception,
):
    if lobby:
        lobby_gateway = FakeLobbyGateway({lobby.id: lobby})
    else:
        lobby_gateway = FakeLobbyGateway()

    game_gateway = FakeGameGateway()
    event_publisher = FakeEventPublisher()
    task_scheduler = FakeTaskScheduler()

    command_processor = CreateGameProcessor(
        create_game=CreateGame(),
        lobby_gateway=lobby_gateway,
        game_gateway=game_gateway,
        event_publisher=event_publisher,
        task_scheduler=task_scheduler,
        transaction_manager=AsyncMock(),
        identity_provider=FakeIdentityProvider(_CURRENT_USER_ID),
    )

    with pytest.raises(expected_error):
        await command_processor.process(command)

    assert not event_publisher.events
    assert not task_scheduler.tasks
