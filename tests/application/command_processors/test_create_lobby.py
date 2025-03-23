# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from unittest.mock import AsyncMock
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
    ConnectFourRuleSet,
    ConnectFourLobby,
    CreateLobby,
    Lobby,
    ConnectFourGame,
    Game,
)
from connection_hub.application import (
    LobbyCreatedEvent,
    RemoveFromLobbyTask,
    CreateLobbyCommand,
    CreateLobbyProcessor,
    CurrentUserInLobbyError,
    CurrentUserInGameError,
    InvalidLobbyNameError,
    InvalidLobbyRuleSetError,
    InvalidLobbyPasswordError,
)
from .fakes import (
    ANY_LOBBY_ID,
    ANY_DATETIME,
    ANY_STR,
    FakeLobbyGateway,
    FakeGameGateway,
    FakeEventPublisher,
    FakeTaskScheduler,
    FakeCentrifugoClient,
    FakeIdentityProvider,
)


_CURRENT_USER_ID: Final = UserId(uuid7())
_OTHER_USER_ID: Final = UserId(uuid7())

_LOBBY_ID: Final = LobbyId(uuid7())
_NAME: Final = "Connect Four for money!!"
_PASSWORD: Final = "12345"
_TIME_FOR_EACH_PLAYER: Final = timedelta(minutes=3)
_CONNECT_FOUR_RULE_SET: Final = ConnectFourRuleSet(
    time_for_each_player=_TIME_FOR_EACH_PLAYER,
)

_GAME_ID: Final = GameId(uuid7())
_CURRENT_PLAYER_STATE_ID: Final = PlayerStateId(uuid7())
_OTHER_PLAYER_STATE_ID: Final = PlayerStateId(uuid7())


async def test_create_lobby_processor():
    lobby_gateway = FakeLobbyGateway()
    event_publisher = FakeEventPublisher()
    task_scheduler = FakeTaskScheduler()
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
        task_scheduler=task_scheduler,
        centrifugo_client=centrifugo_client,
        transaction_manager=AsyncMock(),
        identity_provider=FakeIdentityProvider(_CURRENT_USER_ID),
    )

    await command_processor.process(command)

    expected_lobby = ConnectFourLobby(
        id=ANY_LOBBY_ID,
        name=_NAME,
        users={_CURRENT_USER_ID: UserRole.ADMIN},
        admin_role_transfer_queue=[],
        password=_PASSWORD,
        time_for_each_player=_TIME_FOR_EACH_PLAYER,
    )
    assert expected_lobby in lobby_gateway.lobbies

    expected_event = LobbyCreatedEvent(
        lobby_id=ANY_LOBBY_ID,
        name=_NAME,
        admin_id=_CURRENT_USER_ID,
        has_password=True,
        rule_set=_CONNECT_FOUR_RULE_SET,
    )
    assert expected_event in event_publisher.events

    expected_task = RemoveFromLobbyTask(
        id=ANY_STR,
        execute_at=ANY_DATETIME,
        lobby_id=ANY_LOBBY_ID,
        user_id=_CURRENT_USER_ID,
    )
    assert expected_task in task_scheduler.tasks

    expected_first_centrifugo_publication = {
        "type": "lobby_created",
        "lobby_id": ANY_STR,
        "name": _NAME,
        "rule_set": {
            "type": "connect_four",
            "time_for_each_player": _TIME_FOR_EACH_PLAYER.total_seconds(),
        },
    }
    assert (
        centrifugo_client.publications[f"#{_CURRENT_USER_ID.hex}"]
        == expected_first_centrifugo_publication
    )

    expected_second_centrifugo_publication = {
        "type": "lobby_created",
        "lobby_id": ANY_STR,
        "name": _NAME,
        "has_password": True,
        "rule_set": {
            "type": "connect_four",
            "time_for_each_player": _TIME_FOR_EACH_PLAYER.total_seconds(),
        },
    }
    assert (
        centrifugo_client.publications["lobby_browser"]
        == expected_second_centrifugo_publication
    )


@pytest.mark.parametrize(
    ["lobby", "game", "command", "expected_error"],
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
            CreateLobbyCommand(
                name=_NAME,
                rule_set=_CONNECT_FOUR_RULE_SET,
                password=_PASSWORD,
            ),
            CurrentUserInLobbyError,
        ],
        [
            None,
            ConnectFourGame(
                id=_GAME_ID,
                players={
                    _CURRENT_USER_ID: PlayerState(
                        id=_CURRENT_PLAYER_STATE_ID,
                        status=PlayerStatus.CONNECTED,
                        time_left=timedelta(seconds=40),
                    ),
                    _OTHER_USER_ID: PlayerState(
                        id=_OTHER_PLAYER_STATE_ID,
                        status=PlayerStatus.CONNECTED,
                        time_left=timedelta(seconds=40),
                    ),
                },
                created_at=datetime.now(timezone.utc),
                time_for_each_player=_TIME_FOR_EACH_PLAYER,
            ),
            CreateLobbyCommand(
                name=_NAME,
                rule_set=_CONNECT_FOUR_RULE_SET,
                password=_PASSWORD,
            ),
            CurrentUserInGameError,
        ],
        # Password has too few characters ( < 3 )
        [
            None,
            None,
            CreateLobbyCommand(
                name="ab",
                rule_set=_CONNECT_FOUR_RULE_SET,
                password=_PASSWORD,
            ),
            InvalidLobbyNameError,
        ],
        # Password has too much characters ( > 128 )
        [
            None,
            None,
            CreateLobbyCommand(
                name="a" * 129,
                rule_set=_CONNECT_FOUR_RULE_SET,
                password=_PASSWORD,
            ),
            InvalidLobbyNameError,
        ],
        # Rule set has too little time for each player ( < 30 sec. )
        [
            None,
            None,
            CreateLobbyCommand(
                name=_NAME,
                rule_set=(
                    ConnectFourRuleSet(
                        time_for_each_player=timedelta(seconds=29),
                    )
                ),
                password=_PASSWORD,
            ),
            InvalidLobbyRuleSetError,
        ],
        # Rule set has too much time for each player ( > 3 min. )
        [
            None,
            None,
            CreateLobbyCommand(
                name=_NAME,
                rule_set=(
                    ConnectFourRuleSet(
                        time_for_each_player=timedelta(minutes=3, seconds=1),
                    )
                ),
                password=_PASSWORD,
            ),
            InvalidLobbyRuleSetError,
        ],
        # Password has too few characters ( < 3 )
        [
            None,
            None,
            CreateLobbyCommand(
                name=_NAME,
                rule_set=_CONNECT_FOUR_RULE_SET,
                password="a",
            ),
            InvalidLobbyPasswordError,
        ],
        # Password has too many characters ( > 64 )
        [
            None,
            None,
            CreateLobbyCommand(
                name=_NAME,
                rule_set=_CONNECT_FOUR_RULE_SET,
                password="a" * 65,
            ),
            InvalidLobbyPasswordError,
        ],
    ],
)
async def test_create_lobby_processor_error(
    lobby: Lobby | None,
    game: Game | None,
    command: CreateLobbyCommand,
    expected_error: Exception,
):
    if lobby:
        lobby_gateway = FakeLobbyGateway({lobby.id: lobby})
    else:
        lobby_gateway = FakeLobbyGateway()

    if game:
        game_gateway = FakeGameGateway({game.id: game})
    else:
        game_gateway = FakeGameGateway()

    event_publisher = FakeEventPublisher()
    task_scheduler = FakeTaskScheduler()
    centrifugo_client = FakeCentrifugoClient()

    command_processor = CreateLobbyProcessor(
        create_lobby=CreateLobby(),
        lobby_gateway=lobby_gateway,
        game_gateway=game_gateway,
        event_publisher=event_publisher,
        task_scheduler=task_scheduler,
        centrifugo_client=centrifugo_client,
        transaction_manager=AsyncMock(),
        identity_provider=FakeIdentityProvider(_CURRENT_USER_ID),
    )

    with pytest.raises(expected_error):
        await command_processor.process(command)

    assert not event_publisher.events
    assert not task_scheduler.tasks
    assert not centrifugo_client.publications
