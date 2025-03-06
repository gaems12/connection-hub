# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from datetime import datetime, timedelta, timezone
from typing import Final

import pytest
from redis.asyncio.client import Redis, Pipeline
from uuid_extensions import uuid7

from connection_hub.domain import (
    GameId,
    UserId,
    PlayerStateId,
    PlayerStatus,
    PlayerState,
    ConnectFourGame,
)
from connection_hub.infrastructure import (
    common_retort_factory,
    LockManagerConfig,
    LockManager,
    GameMapperConfig,
    GameMapper,
    RedisTransactionManager,
)


_GAME_ID: Final = GameId(uuid7())

_FIRST_PLAYER_ID: Final = UserId(uuid7())
_SECOND_PLAYER_ID: Final = UserId(uuid7())


@pytest.mark.usefixtures("clear_redis")
async def test_game_mapper(
    redis: Redis,
    redis_pipeline: Pipeline,
):
    lock_manager_config = LockManagerConfig(timedelta(seconds=3))
    lock_manager = LockManager(
        redis=redis,
        config=lock_manager_config,
    )

    game_mapper_config = GameMapperConfig(timedelta(days=1))
    game_mapper = GameMapper(
        redis=redis,
        redis_pipeline=redis_pipeline,
        common_retort=common_retort_factory(),
        lock_manager=lock_manager,
        config=game_mapper_config,
    )

    transaction_manager = RedisTransactionManager(
        redis_pipeline=redis_pipeline,
        lock_manager=lock_manager,
    )

    game = await game_mapper.by_id(_GAME_ID)
    assert game is None

    players = {
        _FIRST_PLAYER_ID: PlayerState(
            id=PlayerStateId(uuid7()),
            status=PlayerStatus.CONNECTED,
            time_left=timedelta(minutes=3),
        ),
        _SECOND_PLAYER_ID: PlayerState(
            id=PlayerStateId(uuid7()),
            status=PlayerStatus.CONNECTED,
            time_left=timedelta(minutes=3),
        ),
    }
    new_game = ConnectFourGame(
        id=_GAME_ID,
        players=players,
        created_at=datetime.now(timezone.utc),
        time_for_each_player=timedelta(minutes=3),
    )
    await game_mapper.save(new_game)
    await transaction_manager.commit()

    game_from_database = await game_mapper.by_id(
        id=_GAME_ID,
        acquire=True,
    )
    assert game_from_database == new_game

    updated_game = new_game
    updated_game.players.pop(_SECOND_PLAYER_ID)
    await game_mapper.update(updated_game)
    await transaction_manager.commit()

    game_from_database = await game_mapper.by_player_id(
        player_id=_FIRST_PLAYER_ID,
        acquire=True,
    )
    assert game_from_database == updated_game

    game_from_database = await game_mapper.by_player_id(
        player_id=_SECOND_PLAYER_ID,
        acquire=True,
    )
    assert game_from_database is None

    await game_mapper.delete(updated_game)
    await transaction_manager.commit()

    game_from_database = await game_mapper.by_id(
        id=_GAME_ID,
        acquire=True,
    )
    assert game_from_database is None
