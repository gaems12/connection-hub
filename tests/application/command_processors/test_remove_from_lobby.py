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
    LobbyId,
    UserId,
    ConnectFourLobby,
    Lobby,
    RemoveFromLobby,
)
from connection_hub.application import (
    UserRemovedFromLobbyEvent,
    RemoveFromLobbyTask,
    RemoveFromLobbyCommand,
    RemoveFromLobbyProcessor,
    LobbyDoesNotExistError,
    UserNotInLobbyError,
)
from .fakes import (
    FakeLobbyGateway,
    FakeEventPublisher,
    FakeTaskScheduler,
    FakeCentrifugoClient,
)


_FIRST_USER_ID: Final = UserId(uuid7())
_SECOND_USER_ID: Final = UserId(uuid7())
_THIRD_USER_ID: Final = UserId(uuid7())

_LOBBY_ID: Final = LobbyId(uuid7())
_NAME: Final = "Connect Four for money!!"
_PASSWORD: Final = "12345"
_TIME_FOR_EACH_PLAYER: Final = timedelta(minutes=1)


async def test_remove_from_lobby():
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

    task = RemoveFromLobbyTask(
        id=f"remove_from_lobby:{_LOBBY_ID.hex}:{_FIRST_USER_ID.hex}",
        execute_at=datetime.now(timezone.utc),
        lobby_id=_LOBBY_ID,
        user_id=_FIRST_USER_ID,
    )
    task_scheduler = FakeTaskScheduler([task])

    lobby_gateway = FakeLobbyGateway([lobby])
    event_publisher = FakeEventPublisher()
    centrifugo_client = FakeCentrifugoClient(
        subscriptons={_FIRST_USER_ID.hex: [f"lobbies:{_LOBBY_ID.hex}"]},
    )

    command = RemoveFromLobbyCommand(
        lobby_id=_LOBBY_ID,
        user_id=_FIRST_USER_ID,
    )
    command_processor = RemoveFromLobbyProcessor(
        remove_from_lobby=RemoveFromLobby(),
        lobby_gateway=lobby_gateway,
        event_publisher=event_publisher,
        task_scheduler=task_scheduler,
        centrifugo_client=centrifugo_client,
        transaction_manager=AsyncMock(),
    )

    await command_processor.process(command)

    expected_lobby = lobby = ConnectFourLobby(
        id=_LOBBY_ID,
        name=_NAME,
        users={_SECOND_USER_ID: UserRole.ADMIN},
        admin_role_transfer_queue=[],
        password=_PASSWORD,
        time_for_each_player=_TIME_FOR_EACH_PLAYER,
    )
    assert expected_lobby == lobby

    expected_event = UserRemovedFromLobbyEvent(
        lobby_id=_LOBBY_ID,
        user_id=_FIRST_USER_ID,
        new_admin_id=_SECOND_USER_ID,
    )
    assert expected_event in event_publisher.events

    assert task not in task_scheduler.tasks

    expected_centrifugo_publication = {
        "type": "user_removed",
        "user_id": _FIRST_USER_ID.hex,
        "new_admin_id": _SECOND_USER_ID.hex,
    }
    assert (
        centrifugo_client.publications[f"lobbies:{_LOBBY_ID.hex}"]
        == expected_centrifugo_publication
    )

    assert (
        f"lobbies:{_LOBBY_ID.hex}"
        not in centrifugo_client.subscriptions[_FIRST_USER_ID.hex]
    )


@pytest.mark.parametrize(
    ["lobby", "command", "expected_error"],
    [
        [
            None,
            RemoveFromLobbyCommand(
                lobby_id=_LOBBY_ID,
                user_id=_FIRST_USER_ID,
            ),
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
            RemoveFromLobbyCommand(
                lobby_id=_LOBBY_ID,
                user_id=_THIRD_USER_ID,
            ),
            UserNotInLobbyError,
        ],
    ],
)
async def test_remove_from_lobby_errors(
    lobby: Lobby | None,
    command: RemoveFromLobbyCommand,
    expected_error: Exception,
):
    lobby_gateway = FakeLobbyGateway([lobby] if lobby else None)
    event_publisher = FakeEventPublisher()
    task_scheduler = FakeTaskScheduler()
    centrifugo_client = FakeCentrifugoClient()

    command_processor = RemoveFromLobbyProcessor(
        remove_from_lobby=RemoveFromLobby(),
        lobby_gateway=lobby_gateway,
        event_publisher=event_publisher,
        task_scheduler=task_scheduler,
        centrifugo_client=centrifugo_client,
        transaction_manager=AsyncMock(),
    )

    with pytest.raises(expected_error):
        await command_processor.process(command)

    assert not event_publisher.events
    assert not task_scheduler.tasks
    assert not centrifugo_client.publications
