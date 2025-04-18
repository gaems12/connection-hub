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
    UserId,
    LobbyId,
    ConnectFourLobby,
    Lobby,
    KickFromLobby,
    UserIsNotAdminError,
    UserIsTryingKickHimselfError,
)
from connection_hub.application import (
    UserKickedFromLobbyEvent,
    RemoveFromLobbyTask,
    KickFromLobbyCommand,
    KickFromLobbyProcessor,
    LobbyDoesNotExistError,
    UserNotInLobbyError,
)
from .fakes import (
    FakeLobbyGateway,
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
_TIME_FOR_EACH_PLAYER: Final = timedelta(minutes=1)


async def test_kick_from_lobby_processor():
    lobby = ConnectFourLobby(
        id=_LOBBY_ID,
        name=_NAME,
        users={
            _CURRENT_USER_ID: UserRole.ADMIN,
            _OTHER_USER_ID: UserRole.REGULAR_MEMBER,
        },
        admin_role_transfer_queue=[_OTHER_USER_ID],
        password=_PASSWORD,
        time_for_each_player=_TIME_FOR_EACH_PLAYER,
    )

    task = RemoveFromLobbyTask(
        id=f"remove_from_lobby:{_LOBBY_ID.hex}:{_CURRENT_USER_ID.hex}",
        execute_at=datetime.now(timezone.utc) + timedelta(seconds=15),
        lobby_id=_LOBBY_ID,
        user_id=_CURRENT_USER_ID,
    )
    task_scheduler = FakeTaskScheduler([task])

    lobby_gateway = FakeLobbyGateway([lobby])
    event_publisher = FakeEventPublisher()
    centrifugo_client = FakeCentrifugoClient(
        subscriptons={_OTHER_USER_ID.hex: [f"lobbies:{_LOBBY_ID.hex}"]},
    )

    command = KickFromLobbyCommand(user_id=_OTHER_USER_ID)
    command_processor = KickFromLobbyProcessor(
        kick_from_lobby=KickFromLobby(),
        lobby_gateway=lobby_gateway,
        event_publisher=event_publisher,
        task_scheduler=task_scheduler,
        centrifugo_client=centrifugo_client,
        tranaction_manager=AsyncMock(),
        identity_provider=FakeIdentityProvider(_CURRENT_USER_ID),
    )

    await command_processor.process(command)

    expected_lobby = ConnectFourLobby(
        id=_LOBBY_ID,
        name=_NAME,
        users={_CURRENT_USER_ID: UserRole.ADMIN},
        admin_role_transfer_queue=[],
        password=_PASSWORD,
        time_for_each_player=_TIME_FOR_EACH_PLAYER,
    )
    assert expected_lobby == lobby

    expected_event = UserKickedFromLobbyEvent(
        lobby_id=_LOBBY_ID,
        user_id=_OTHER_USER_ID,
    )
    assert expected_event in event_publisher.events

    assert task not in task_scheduler.tasks

    expected_centrifugo_publication = {
        "type": "user_kicked",
        "lobby_id": _LOBBY_ID.hex,
        "user_id": _OTHER_USER_ID.hex,
    }
    assert (
        centrifugo_client.publications[f"lobbies:{_LOBBY_ID.hex}"]
        == expected_centrifugo_publication
    )

    assert (
        f"lobbies:{_LOBBY_ID.hex}"
        not in centrifugo_client.subscriptions[_OTHER_USER_ID.hex]
    )


@pytest.mark.parametrize(
    ["lobby", "command", "expected_error"],
    [
        [
            None,
            KickFromLobbyCommand(user_id=_OTHER_USER_ID),
            LobbyDoesNotExistError,
        ],
        [
            ConnectFourLobby(
                id=_LOBBY_ID,
                name=_NAME,
                users={_CURRENT_USER_ID: UserRole.ADMIN},
                admin_role_transfer_queue=[],
                password=_PASSWORD,
                time_for_each_player=_TIME_FOR_EACH_PLAYER,
            ),
            KickFromLobbyCommand(user_id=_OTHER_USER_ID),
            UserNotInLobbyError,
        ],
        [
            ConnectFourLobby(
                id=_LOBBY_ID,
                name=_NAME,
                users={
                    _OTHER_USER_ID: UserRole.ADMIN,
                    _CURRENT_USER_ID: UserRole.REGULAR_MEMBER,
                },
                admin_role_transfer_queue=[_CURRENT_USER_ID],
                password=_PASSWORD,
                time_for_each_player=_TIME_FOR_EACH_PLAYER,
            ),
            KickFromLobbyCommand(user_id=_OTHER_USER_ID),
            UserIsNotAdminError,
        ],
        [
            ConnectFourLobby(
                id=_LOBBY_ID,
                name=_NAME,
                users={
                    _CURRENT_USER_ID: UserRole.ADMIN,
                    _OTHER_USER_ID: UserRole.REGULAR_MEMBER,
                },
                admin_role_transfer_queue=[_OTHER_USER_ID],
                password=_PASSWORD,
                time_for_each_player=_TIME_FOR_EACH_PLAYER,
            ),
            KickFromLobbyCommand(user_id=_CURRENT_USER_ID),
            UserIsTryingKickHimselfError,
        ],
    ],
)
async def test_kick_from_lobby_processor_errors(
    lobby: Lobby | None,
    command: KickFromLobbyCommand,
    expected_error: Exception,
):
    lobby_gateway = FakeLobbyGateway([lobby] if lobby else None)
    event_publisher = FakeEventPublisher()
    task_scheduler = FakeTaskScheduler()
    centrifugo_client = FakeCentrifugoClient()

    command_processor = KickFromLobbyProcessor(
        kick_from_lobby=KickFromLobby(),
        lobby_gateway=lobby_gateway,
        event_publisher=event_publisher,
        task_scheduler=task_scheduler,
        centrifugo_client=centrifugo_client,
        tranaction_manager=AsyncMock(),
        identity_provider=FakeIdentityProvider(_CURRENT_USER_ID),
    )

    with pytest.raises(expected_error):
        await command_processor.process(command)

    assert not event_publisher.events
    assert not task_scheduler.tasks
    assert not centrifugo_client.publications
