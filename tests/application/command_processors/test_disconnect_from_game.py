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
    DisconnectFromGame,
    PlayerIsDisconnectedError,
)
from connection_hub.application import (
    TryToDisqualifyPlayerTask,
    ConnectFourGamePlayerDisconnectedEvent,
    DisconnectFromGameProcessor,
    UserNotInGameError,
)
from .fakes import (
    ANY_PLAYER_STATE_ID,
    ANY_DATETIME,
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

_GAME_ID: Final = GameId(uuid7())
_CREATED_AT: Final = datetime.now(timezone.utc)
_TIME_FOR_EACH_PLAYER: Final = timedelta(minutes=1)


async def test_disconnect_from_game_processor():
    game = ConnectFourGame(
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
        created_at=_CREATED_AT,
        time_for_each_player=_TIME_FOR_EACH_PLAYER,
    )

    game_gateway = FakeGameGateway({game.id: game})
    task_scheduler = FakeTaskScheduler()
    event_publisher = FakeEventPublisher()
    centrifugo_client = FakeCentrifugoClient()

    processor = DisconnectFromGameProcessor(
        disconnect_from_game=DisconnectFromGame(),
        game_gateway=game_gateway,
        task_scheduler=task_scheduler,
        event_publisher=event_publisher,
        centrifugo_client=centrifugo_client,
        transaction_manager=AsyncMock(),
        identity_provider=FakeIdentityProvider(_CURRENT_USER_ID),
    )

    await processor.process()

    expected_game = ConnectFourGame(
        id=_GAME_ID,
        players={
            _CURRENT_USER_ID: PlayerState(
                id=ANY_PLAYER_STATE_ID,
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
    assert expected_game == game

    expected_task = TryToDisqualifyPlayerTask(
        id=ANY_PLAYER_STATE_ID,
        execute_at=ANY_DATETIME,
        game_id=_GAME_ID,
        player_id=_CURRENT_USER_ID,
        player_state_id=ANY_PLAYER_STATE_ID,
    )
    assert expected_task in task_scheduler.tasks

    expected_event = ConnectFourGamePlayerDisconnectedEvent(
        game_id=_GAME_ID,
        player_id=_CURRENT_USER_ID,
    )
    assert expected_event in event_publisher.events

    expected_centrifugo_publication = {
        "type": "player_disconnected",
        "player_id": _CURRENT_USER_ID.hex,
    }
    assert (
        centrifugo_client.publications[f"games:{_GAME_ID.hex}"]
        == expected_centrifugo_publication
    )


@pytest.mark.parametrize(
    ["game", "expected_error"],
    [
        [
            None,
            UserNotInGameError,
        ],
        [
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
            PlayerIsDisconnectedError,
        ],
    ],
)
async def test_disconnect_from_game_processor_errors(
    game: Game | None,
    expected_error: Exception,
):
    if game:
        game_gateway = FakeGameGateway({game.id: game})
    else:
        game_gateway = FakeGameGateway()

    task_scheduler = FakeTaskScheduler()
    event_publisher = FakeEventPublisher()
    centrifugo_client = FakeCentrifugoClient()

    processor = DisconnectFromGameProcessor(
        disconnect_from_game=DisconnectFromGame(),
        game_gateway=game_gateway,
        task_scheduler=task_scheduler,
        event_publisher=event_publisher,
        centrifugo_client=centrifugo_client,
        transaction_manager=AsyncMock(),
        identity_provider=FakeIdentityProvider(_CURRENT_USER_ID),
    )

    with pytest.raises(expected_error):
        await processor.process()

    assert not task_scheduler.tasks
    assert not event_publisher.events
    assert not centrifugo_client.publications
