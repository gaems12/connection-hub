# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from datetime import timedelta
from typing import Final

import pytest
from redis.asyncio.client import Redis, Pipeline
from uuid_extensions import uuid7

from connection_hub.domain import (
    LobbyId,
    UserId,
    UserRole,
    FourInARowLobby,
)
from connection_hub.infrastructure import (
    common_retort_factory,
    LockManagerConfig,
    LockManager,
    LobbyMapperConfig,
    LobbyMapper,
    RedisTransactionManager,
)


_LOBBY_ID: Final = LobbyId(uuid7())

_FIRST_USER_ID: Final = UserId(uuid7())
_SECOND_USER_ID: Final = UserId(uuid7())


@pytest.mark.usefixtures("clear_redis")
async def test_lobby_mapper(
    redis: Redis,
    redis_pipeline: Pipeline,
):
    lock_manager_config = LockManagerConfig(timedelta(seconds=3))
    lock_manager = LockManager(
        redis=redis,
        config=lock_manager_config,
    )

    lobby_mapper_config = LobbyMapperConfig(timedelta(days=1))
    lobby_mapper = LobbyMapper(
        redis=redis,
        redis_pipeline=redis_pipeline,
        common_retort=common_retort_factory(),
        lock_manager=lock_manager,
        config=lobby_mapper_config,
    )

    transaction_manager = RedisTransactionManager(
        redis_pipeline=redis_pipeline,
        lock_manager=lock_manager,
    )

    lobby = await lobby_mapper.by_id(_LOBBY_ID)
    assert lobby is None

    new_lobby = FourInARowLobby(
        id=_LOBBY_ID,
        name="fake_lobby",
        users={
            _FIRST_USER_ID: UserRole.ADMIN,
            _SECOND_USER_ID: UserRole.REGULAR_MEMBER,
        },
        admin_role_transfer_queue=[_SECOND_USER_ID],
        password="fake_password",
        time_for_each_player=timedelta(minutes=3),
    )
    await lobby_mapper.save(new_lobby)
    await transaction_manager.commit()

    lobby_from_database = await lobby_mapper.by_id(
        id=new_lobby.id,
        acquire=True,
    )
    assert lobby_from_database == new_lobby

    updated_lobby = new_lobby
    updated_lobby.users.pop(_SECOND_USER_ID)
    updated_lobby.admin_role_transfer_queue.pop()
    await lobby_mapper.update(updated_lobby)
    await transaction_manager.commit()

    lobby_from_database = await lobby_mapper.by_user_id(
        user_id=_FIRST_USER_ID,
        acquire=True,
    )
    assert lobby_from_database == updated_lobby

    lobby_from_database = await lobby_mapper.by_user_id(
        user_id=_SECOND_USER_ID,
        acquire=True,
    )
    assert lobby_from_database is None

    await lobby_mapper.delete(updated_lobby)
    await transaction_manager.commit()

    lobby_from_database = await lobby_mapper.by_id(
        id=_LOBBY_ID,
        acquire=True,
    )
    assert lobby_from_database is None
