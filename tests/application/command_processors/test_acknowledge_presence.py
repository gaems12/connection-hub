# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from datetime import datetime, timedelta, timezone
from typing import Final

import pytest
from uuid_extensions import uuid7

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
    ForceLeaveLobbyTask,
    ForceDisconnectFromGameTask,
    Task,
    AcknowledgePresenceProcessor,
)
from .fakes import (
    FakeLobbyGateway,
    FakeGameGateway,
    FakeTaskScheduler,
    FakeIdentityProvider,
    ANY_DATETIME,
)


_CURRENT_USER_ID: Final = UserId(uuid7())
_CURRENT_PLAYER_STATE_ID: Final = PlayerStateId(uuid7())

_OTHER_USER_ID: Final = UserId(uuid7())
_OTHER_PLAYER_STATE_ID: Final = PlayerStateId(uuid7())

_LOBBY_ID: Final = LobbyId(uuid7())
_NAME: Final = "Connect Four for money!!"
_PASSWORD: Final = "12345"
_TIME_FOR_EACH_PLAYER: Final = timedelta(minutes=1)

_GAME_ID: Final = GameId(uuid7())
_CREATED_AT: Final = datetime.now(timezone.utc)


@pytest.mark.parametrize(
    ["lobby", "game", "expected_task"],
    [
        [
            ConnectFourLobby(
                id=_LOBBY_ID,
                name=_NAME,
                users={_CURRENT_USER_ID: UserRole.ADMIN},
                admin_role_transfer_queue=[],
                password=_PASSWORD,
                time_for_each_player=_TIME_FOR_EACH_PLAYER,
            ),
            None,
            ForceLeaveLobbyTask(
                id=(
                    "force_leave_lobby:"
                    f"{_LOBBY_ID.hex}:{_CURRENT_USER_ID.hex}"
                ),
                execute_at=ANY_DATETIME,
                lobby_id=_LOBBY_ID,
                user_id=_CURRENT_USER_ID,
            ),
        ],
        [
            None,
            ConnectFourGame(
                id=_GAME_ID,
                players={
                    _CURRENT_USER_ID: PlayerState(
                        id=_CURRENT_PLAYER_STATE_ID,
                        status=PlayerStatus.DISCONNECTED,
                        time_left=timedelta(seconds=40),
                    ),
                    _OTHER_USER_ID: PlayerState(
                        id=_OTHER_PLAYER_STATE_ID,
                        status=PlayerStatus.CONNECTED,
                        time_left=timedelta(seconds=40),
                    ),
                },
                created_at=_CREATED_AT,
                time_for_each_player=_TIME_FOR_EACH_PLAYER,
            ),
            ForceDisconnectFromGameTask(
                id=(
                    "force_disconnect_from_game:"
                    f"{_GAME_ID.hex}:{_CURRENT_USER_ID.hex}"
                ),
                execute_at=ANY_DATETIME,
                game_id=_GAME_ID,
                player_id=_CURRENT_USER_ID,
            ),
        ],
    ],
)
async def test_acknowledge_presence(
    lobby: Lobby | None,
    game: Game | None,
    expected_task: Task,
):
    if lobby:
        lobby_gateway = FakeLobbyGateway({lobby.id: lobby})
    else:
        lobby_gateway = FakeLobbyGateway()

    if game:
        game_gateway = FakeGameGateway({game.id: game})
    else:
        game_gateway = FakeGameGateway()

    task_scheduler = FakeTaskScheduler()

    processor = AcknowledgePresenceProcessor(
        lobby_gateway=lobby_gateway,
        game_gateway=game_gateway,
        task_scheduler=task_scheduler,
        identity_provider=FakeIdentityProvider(_CURRENT_USER_ID),
    )

    await processor.process()

    assert expected_task in task_scheduler.tasks
