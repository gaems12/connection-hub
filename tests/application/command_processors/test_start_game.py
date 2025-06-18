# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from unittest.mock import AsyncMock
from datetime import datetime, timedelta, timezone
from typing import Final

import pytest
from uuid_extensions import uuid7

from connection_hub.application.common.exceptions import GameDoesNotExistError
from connection_hub.domain import (
    UserRole,
    PlayerStatus,
    LobbyId,
    GameId,
    UserId,
    PlayerStateId,
    PlayerState,
    ConnectFourLobby,
    Lobby,
    ConnectFourGame,
    Game,
)
from connection_hub.application import (
    RemoveFromLobbyTask,
    DisconnectFromGameTask,
    StartGameCommand,
    StartGameProcessor,
    LobbyDoesNotExistError,
)
from .fakes import (
    ANY_DATETIME,
    FakeLobbyGateway,
    FakeGameGateway,
    FakeTaskScheduler,
    FakeCentrifugoClient,
)


_FIRST_USER_ID: Final = UserId(uuid7())
_FIRST_PLAYER_STATE_ID: Final = PlayerStateId(uuid7())

_SECOND_USER_ID: Final = UserId(uuid7())
_SECOND_PLAYER_STATE_ID: Final = PlayerStateId(uuid7())

_LOBBY_ID: Final = LobbyId(uuid7())
_GAME_ID: Final = GameId(uuid7())
_NAME: Final = "Connect Four for money!!"
_PASSWORD: Final = "12345"
_TIME_FOR_EACH_PLAYER: Final = timedelta(minutes=1)
_CREATED_AT: Final = datetime.now(timezone.utc)


async def test_start_game_processor():
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
    game = ConnectFourGame(
        id=_GAME_ID,
        players={
            _FIRST_USER_ID: PlayerState(
                id=_FIRST_PLAYER_STATE_ID,
                status=PlayerStatus.CONNECTED,
                time_left=timedelta(seconds=40),
            ),
            _SECOND_USER_ID: PlayerState(
                id=_SECOND_PLAYER_STATE_ID,
                status=PlayerStatus.CONNECTED,
                time_left=timedelta(seconds=40),
            ),
        },
        created_at=_CREATED_AT,
        time_for_each_player=_TIME_FOR_EACH_PLAYER,
    )

    first_task = RemoveFromLobbyTask(
        id=f"remove_from_lobby:{_LOBBY_ID.hex}:{_FIRST_USER_ID.hex}",
        execute_at=datetime.now(timezone.utc) + timedelta(seconds=15),
        lobby_id=_LOBBY_ID,
        user_id=_FIRST_USER_ID,
    )
    second_task = RemoveFromLobbyTask(
        id=f"remove_from_lobby:{_LOBBY_ID.hex}:{_SECOND_USER_ID.hex}",
        execute_at=datetime.now(timezone.utc) + timedelta(seconds=15),
        lobby_id=_LOBBY_ID,
        user_id=_SECOND_USER_ID,
    )
    task_scheduler = FakeTaskScheduler([first_task, second_task])

    lobby_gateway = FakeLobbyGateway([lobby])
    game_gateway = FakeGameGateway([game])
    centrifugo_client = FakeCentrifugoClient()

    command = StartGameCommand(
        game_id=_GAME_ID,
        lobby_id=_LOBBY_ID,
    )
    command_processor = StartGameProcessor(
        lobby_gateway=lobby_gateway,
        game_gateway=game_gateway,
        task_scheduler=task_scheduler,
        centrifugo_client=centrifugo_client,
        transaction_manager=AsyncMock(),
    )

    await command_processor.process(command)

    assert lobby not in lobby_gateway.lobbies

    assert first_task not in task_scheduler.tasks
    assert second_task not in task_scheduler.tasks

    first_expected_task = DisconnectFromGameTask(
        id=f"disconnect_from_game:{_GAME_ID.hex}:{_FIRST_USER_ID.hex}",
        execute_at=ANY_DATETIME,
        game_id=_GAME_ID,
        player_id=_FIRST_USER_ID,
    )
    assert first_expected_task in task_scheduler.tasks

    second_expected_task = DisconnectFromGameTask(
        id=f"disconnect_from_game:{_GAME_ID.hex}:{_SECOND_USER_ID.hex}",
        execute_at=ANY_DATETIME,
        game_id=_GAME_ID,
        player_id=_SECOND_USER_ID,
    )
    assert second_expected_task in task_scheduler.tasks

    expected_centrifugo_publication = {
        "type": "lobby_removed",
        "lobby_id": _LOBBY_ID.hex,
    }
    assert (
        centrifugo_client.publications["lobby_browser"]
        == expected_centrifugo_publication
    )


@pytest.mark.parametrize(
    ["lobby", "game", "command", "expected_error"],
    [
        [
            None,
            None,
            StartGameCommand(game_id=_GAME_ID, lobby_id=_LOBBY_ID),
            LobbyDoesNotExistError,
        ],
        [
            ConnectFourLobby(
                id=_LOBBY_ID,
                name=_NAME,
                users={
                    _FIRST_USER_ID: UserRole.ADMIN,
                    _SECOND_USER_ID: UserRole.REGULAR_MEMBER,
                },
                admin_role_transfer_queue=[_SECOND_USER_ID],
                password=_PASSWORD,
                time_for_each_player=_TIME_FOR_EACH_PLAYER,
            ),
            None,
            StartGameCommand(game_id=_GAME_ID, lobby_id=_LOBBY_ID),
            GameDoesNotExistError,
        ],
    ],
)
async def test_start_game_processor_errors(
    lobby: Lobby | None,
    game: Game | None,
    command: StartGameCommand,
    expected_error: Exception,
):
    lobby_gateway = FakeLobbyGateway([lobby] if lobby else None)
    game_gateway = FakeGameGateway([game] if game else None)
    task_scheduler = FakeTaskScheduler()
    centrifugo_client = FakeCentrifugoClient()

    command_processor = StartGameProcessor(
        lobby_gateway=lobby_gateway,
        game_gateway=game_gateway,
        task_scheduler=task_scheduler,
        centrifugo_client=centrifugo_client,
        transaction_manager=AsyncMock(),
    )

    with pytest.raises(expected_error):
        await command_processor.process(command)

    assert not task_scheduler.tasks
    assert not centrifugo_client.publications
