# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from unittest.mock import AsyncMock
from datetime import datetime, timedelta, timezone
from typing import Final

from uuid_extensions import uuid7

from connection_hub.domain import (
    PlayerStatus,
    UserId,
    GameId,
    PlayerStateId,
    PlayerState,
    ConnectFourGame,
    TryToDisqualifyPlayer,
)
from connection_hub.application import (
    ConnectFourGamePlayerDisqualifiedEvent,
    TryToDisqualifyPlayerCommand,
    TryToDisqualifyPlayerProcessor,
)
from .fakes import (
    FakeGameGateway,
    FakeTaskScheduler,
    FakeEventPublisher,
    FakeCentrifugoClient,
)


_FIRST_USER_ID: Final = UserId(uuid7())
_FIRST_PLAYER_STATE_ID: Final = PlayerStateId(uuid7())

_SECOND_USER_ID: Final = UserId(uuid7())
_SECOND_PLAYER_STATE_ID: Final = PlayerStateId(uuid7())

_GAME_ID: Final = GameId(uuid7())
_CREATED_AT: Final = datetime.now(timezone.utc)
_TIME_FOR_EACH_PLAYER: Final = timedelta(minutes=1)


async def test_try_to_disqualify_player_processor():
    game = ConnectFourGame(
        id=_GAME_ID,
        players={
            _FIRST_USER_ID: PlayerState(
                id=_FIRST_PLAYER_STATE_ID,
                status=PlayerStatus.DISCONNECTED,
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

    game_gateway = FakeGameGateway({game.id: game})
    event_publisher = FakeEventPublisher()
    centrifugo_client = FakeCentrifugoClient()

    command = TryToDisqualifyPlayerCommand(
        game_id=_GAME_ID,
        player_id=_FIRST_USER_ID,
        player_state_id=_FIRST_PLAYER_STATE_ID,
    )
    command_processor = TryToDisqualifyPlayerProcessor(
        try_to_disqualify_player=TryToDisqualifyPlayer(),
        game_gateway=game_gateway,
        event_publisher=event_publisher,
        task_scheduler=FakeTaskScheduler(),
        centrifugo_client=centrifugo_client,
        transaction_manager=AsyncMock(),
    )

    await command_processor.process(command)

    assert not game_gateway.games

    expected_event = ConnectFourGamePlayerDisqualifiedEvent(
        game_id=_GAME_ID,
        player_id=_FIRST_USER_ID,
    )
    assert expected_event in event_publisher.events

    expected_centrifugo_publication = {
        "type": "player_disqualified",
        "player_id": _FIRST_USER_ID.hex,
    }
    assert (
        centrifugo_client.publications[f"games:{_GAME_ID.hex}"]
        == expected_centrifugo_publication
    )
