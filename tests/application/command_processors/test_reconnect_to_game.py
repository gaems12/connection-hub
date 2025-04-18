# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from unittest.mock import AsyncMock
from datetime import datetime, timedelta, timezone
from typing import Final

import pytest
from uuid_extensions import uuid7

from connection_hub.domain import (
    PlayerStatus,
    UserId,
    GameId,
    PlayerStateId,
    PlayerState,
    ConnectFourGame,
    Game,
    ReconnectToGame,
    UserIsConnectedToGameError,
)
from connection_hub.application import (
    TryToDisqualifyPlayerTask,
    ConnectFourGamePlayerReconnectedEvent,
    ReconnectToGameCommand,
    ReconnectToGameProcessor,
    GameDoesNotExistError,
    CurrentUserNotInGameError,
)
from .fakes import (
    ANY_PLAYER_STATE_ID,
    ANY_TIMEDELTA,
    FakeGameGateway,
    FakeTaskScheduler,
    FakeEventPublisher,
    FakeCentrifugoClient,
    FakeIdentityProvider,
)


_CURRENT_USER_ID: Final = UserId(uuid7())
_CURRENT_PLAYER_STATE_ID: Final = PlayerStateId(uuid7())

_OTHER_USER_ID: Final = UserId(uuid7())
_OTHER_PLAYER_STATE_ID: Final = PlayerStateId(uuid7())

_ANOTHER_USER_ID: Final = UserId(uuid7())
_ANOTHER_PLAYER_STATE_ID: Final = PlayerStateId(uuid7())

_GAME_ID: Final = GameId(uuid7())
_CREATED_AT: Final = datetime.now(timezone.utc)
_TIME_FOR_EACH_PLAYER: Final = timedelta(minutes=1)


async def test_reconnect_to_game_processor():
    game = ConnectFourGame(
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
    )

    game_gateway = FakeGameGateway([game])

    task = TryToDisqualifyPlayerTask(
        id=f"try_to_disqualify_player:{_CURRENT_PLAYER_STATE_ID.hex}",
        execute_at=datetime.now(timezone.utc) + timedelta(seconds=39),
        game_id=_GAME_ID,
        player_id=_CURRENT_USER_ID,
        player_state_id=_CURRENT_PLAYER_STATE_ID,
    )
    task_scheduler = FakeTaskScheduler([task])

    event_publisher = FakeEventPublisher()
    centrifugo_client = FakeCentrifugoClient()

    command = ReconnectToGameCommand(game_id=_GAME_ID)
    command_processor = ReconnectToGameProcessor(
        reconnect_to_game=ReconnectToGame(),
        game_gateway=game_gateway,
        event_publisher=event_publisher,
        task_scheduler=task_scheduler,
        centrifugo_client=centrifugo_client,
        transaction_manager=AsyncMock(),
        identity_provider=FakeIdentityProvider(_CURRENT_USER_ID),
    )

    await command_processor.process(command)

    expected_game = ConnectFourGame(
        id=_GAME_ID,
        players={
            _CURRENT_USER_ID: PlayerState(
                id=ANY_PLAYER_STATE_ID,
                status=PlayerStatus.CONNECTED,
                time_left=ANY_TIMEDELTA,
            ),
            _OTHER_USER_ID: PlayerState(
                id=_OTHER_PLAYER_STATE_ID,
                status=PlayerStatus.CONNECTED,
                time_left=timedelta(seconds=40),
            ),
        },
        created_at=_CREATED_AT,
        time_for_each_player=_TIME_FOR_EACH_PLAYER,
    )
    assert expected_game == game

    assert not task_scheduler.tasks

    expected_event = ConnectFourGamePlayerReconnectedEvent(
        game_id=_GAME_ID,
        player_id=_CURRENT_USER_ID,
    )
    assert expected_event in event_publisher.events

    expected_centrifugo_publication = {
        "type": "player_reconnected",
        "player_id": _CURRENT_USER_ID.hex,
    }
    assert (
        centrifugo_client.publications[f"games:{_GAME_ID.hex}"]
        == expected_centrifugo_publication
    )


@pytest.mark.parametrize(
    ["game", "command", "expected_error"],
    [
        [
            None,
            ReconnectToGameCommand(game_id=_GAME_ID),
            GameDoesNotExistError,
        ],
        [
            ConnectFourGame(
                id=_GAME_ID,
                players={
                    _OTHER_USER_ID: PlayerState(
                        id=_OTHER_PLAYER_STATE_ID,
                        status=PlayerStatus.CONNECTED,
                        time_left=timedelta(seconds=40),
                    ),
                    _ANOTHER_USER_ID: PlayerState(
                        id=_ANOTHER_PLAYER_STATE_ID,
                        status=PlayerStatus.CONNECTED,
                        time_left=timedelta(seconds=40),
                    ),
                },
                created_at=_CREATED_AT,
                time_for_each_player=_TIME_FOR_EACH_PLAYER,
            ),
            ReconnectToGameCommand(game_id=_GAME_ID),
            CurrentUserNotInGameError,
        ],
        [
            ConnectFourGame(
                id=_GAME_ID,
                players={
                    _CURRENT_USER_ID: PlayerState(
                        id=ANY_PLAYER_STATE_ID,
                        status=PlayerStatus.CONNECTED,
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
            ReconnectToGameCommand(game_id=_GAME_ID),
            UserIsConnectedToGameError,
        ],
    ],
)
async def test_reconnect_to_game_processor_errors(
    game: Game | None,
    command: ReconnectToGameCommand,
    expected_error: Exception,
):
    game_gateway = FakeGameGateway([game] if game else None)
    task_scheduler = FakeTaskScheduler()
    event_publisher = FakeEventPublisher()
    centrifugo_client = FakeCentrifugoClient()

    command_processor = ReconnectToGameProcessor(
        reconnect_to_game=ReconnectToGame(),
        game_gateway=game_gateway,
        event_publisher=event_publisher,
        task_scheduler=task_scheduler,
        centrifugo_client=centrifugo_client,
        transaction_manager=AsyncMock(),
        identity_provider=FakeIdentityProvider(_CURRENT_USER_ID),
    )

    with pytest.raises(expected_error):
        await command_processor.process(command)

    assert not task_scheduler.tasks
    assert not event_publisher.events
    assert not centrifugo_client.publications
