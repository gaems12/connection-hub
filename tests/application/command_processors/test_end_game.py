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
)
from connection_hub.application import (
    TryToDisqualifyPlayerTask,
    EndGameCommand,
    EndGameProcessor,
    GameDoesNotExistError,
)
from .fakes import FakeGameGateway, FakeTaskScheduler


_FIRST_USER_ID: Final = UserId(uuid7())
_FIRST_PLAYER_STATE_ID: Final = PlayerStateId(uuid7())

_SECOND_USER_ID: Final = UserId(uuid7())
_SECOND_PLAYER_STATE_ID: Final = PlayerStateId(uuid7())

_GAME_ID: Final = GameId(uuid7())
_CREATED_AT: Final = datetime.now(timezone.utc)
_TIME_FOR_EACH_PLAYER: Final = timedelta(minutes=1)


async def test_end_game_processor():
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

    game_gateway = FakeGameGateway([game])

    task = TryToDisqualifyPlayerTask(
        id=f"try_to_disqualify_player:{_SECOND_PLAYER_STATE_ID.hex}",
        execute_at=datetime.now(timezone.utc) + timedelta(seconds=39),
        game_id=_GAME_ID,
        player_id=_SECOND_USER_ID,
        player_state_id=_SECOND_PLAYER_STATE_ID,
    )
    task_scheduler = FakeTaskScheduler([task])

    command = EndGameCommand(game_id=_GAME_ID)
    command_processor = EndGameProcessor(
        game_gateway=game_gateway,
        task_scheduler=task_scheduler,
        transaction_manager=AsyncMock(),
    )

    await command_processor.process(command)

    assert not game_gateway.games
    assert not task_scheduler.tasks


async def test_end_game_processor_errors():
    command = EndGameCommand(game_id=_GAME_ID)
    command_processor = EndGameProcessor(
        game_gateway=FakeGameGateway(),
        task_scheduler=FakeTaskScheduler(),
        transaction_manager=AsyncMock(),
    )

    with pytest.raises(GameDoesNotExistError):
        await command_processor.process(command)
