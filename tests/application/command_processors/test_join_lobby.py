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
    ConnectFourLobby,
    Lobby,
    ConnectFourGame,
    Game,
    JoinLobby,
    UserLimitReachedError,
    PasswordRequiredError,
    IncorrectPasswordError,
)
from connection_hub.application import (
    UserJoinedLobbyEvent,
    JoinLobbyCommand,
    JoinLobbyProcessor,
    UserInLobbyError,
    UserInGameError,
    LobbyDoesNotExistError,
)
from .fakes import (
    FakeLobbyGateway,
    FakeGameGateway,
    FakeEventPublisher,
    FakeCentrifugoClient,
    FakeIdentityProvider,
)


_CURRENT_USER_ID: Final = UserId(uuid7())
_OTHER_USER_ID: Final = UserId(uuid7())
_ANOTHER_USER_ID: Final = UserId(uuid7())

_LOBBY_ID: Final = LobbyId(uuid7())
_NAME: Final = "Connect Four for money!!"
_PASSWORD: Final = "12345"
_TIME_FOR_EACH_PLAYER: Final = timedelta(minutes=1)

_GAME_ID: Final = GameId(uuid7())
_CREATED_AT: Final = datetime.now(timezone.utc)
_CURRENT_PLAYER_STATE_ID: Final = PlayerStateId(uuid7())
_OTHER_PLAYER_STATE_ID: Final = PlayerStateId(uuid7())
_ANOTHER_PLAYER_STATE_ID: Final = PlayerStateId(uuid7())


async def test_join_lobby_processor():
    lobby = ConnectFourLobby(
        id=_LOBBY_ID,
        name=_NAME,
        users={_OTHER_USER_ID: UserRole.ADMIN},
        admin_role_transfer_queue=[],
        password=_PASSWORD,
        time_for_each_player=_TIME_FOR_EACH_PLAYER,
    )

    lobby_gateway = FakeLobbyGateway({lobby.id: lobby})
    event_publisher = FakeEventPublisher()
    centrifugo_client = FakeCentrifugoClient()

    command = JoinLobbyCommand(
        lobby_id=_LOBBY_ID,
        password=_PASSWORD,
    )
    command_processor = JoinLobbyProcessor(
        join_lobby=JoinLobby(),
        lobby_gateway=lobby_gateway,
        game_gateway=FakeGameGateway({}),
        event_publisher=event_publisher,
        centrifugo_client=centrifugo_client,
        transaction_manager=AsyncMock(),
        identity_provider=FakeIdentityProvider(_CURRENT_USER_ID),
    )

    await command_processor.process(command)

    expected_lobby = ConnectFourLobby(
        id=_LOBBY_ID,
        name=_NAME,
        users={
            _OTHER_USER_ID: UserRole.ADMIN,
            _CURRENT_USER_ID: UserRole.REGULAR_MEMBER,
        },
        admin_role_transfer_queue=[_CURRENT_USER_ID],
        password=_PASSWORD,
        time_for_each_player=_TIME_FOR_EACH_PLAYER,
    )
    assert expected_lobby == lobby

    expected_event = UserJoinedLobbyEvent(
        lobby_id=_LOBBY_ID,
        user_id=_CURRENT_USER_ID,
    )
    assert expected_event in event_publisher.events

    expected_centrifugo_lobby_channel_publication = {
        "type": "user_joined",
        "user_id": _CURRENT_USER_ID.hex,
    }
    assert (
        centrifugo_client.publications[f"lobbies:{_LOBBY_ID.hex}"]
        == expected_centrifugo_lobby_channel_publication
    )

    expected_centrifugo_user_channel_publication = {
        "type": "joined_to_lobby",
        "users": {
            _OTHER_USER_ID.hex: UserRole.ADMIN,
            _CURRENT_USER_ID.hex: UserRole.REGULAR_MEMBER,
        },
    }
    assert (
        centrifugo_client.publications[f"#{_CURRENT_USER_ID.hex}"]
        == expected_centrifugo_user_channel_publication
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
            JoinLobbyCommand(
                lobby_id=LobbyId(uuid7()),
                password=_PASSWORD,
            ),
            UserInLobbyError,
        ],
        [
            ConnectFourLobby(
                id=_LOBBY_ID,
                name=_NAME,
                users={_OTHER_USER_ID: UserRole.ADMIN},
                admin_role_transfer_queue=[],
                password=_PASSWORD,
                time_for_each_player=_TIME_FOR_EACH_PLAYER,
            ),
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
                created_at=_CREATED_AT,
                time_for_each_player=_TIME_FOR_EACH_PLAYER,
            ),
            JoinLobbyCommand(
                lobby_id=_LOBBY_ID,
                password=_PASSWORD,
            ),
            UserInGameError,
        ],
        [
            None,
            None,
            JoinLobbyCommand(
                lobby_id=_LOBBY_ID,
                password=_PASSWORD,
            ),
            LobbyDoesNotExistError,
        ],
        [
            ConnectFourLobby(
                id=_LOBBY_ID,
                name=_NAME,
                users={
                    _OTHER_USER_ID: UserRole.ADMIN,
                    _ANOTHER_PLAYER_STATE_ID: UserRole.REGULAR_MEMBER,
                },
                admin_role_transfer_queue=[_ANOTHER_PLAYER_STATE_ID],
                password=_PASSWORD,
                time_for_each_player=_TIME_FOR_EACH_PLAYER,
            ),
            None,
            JoinLobbyCommand(
                lobby_id=_LOBBY_ID,
                password=_PASSWORD,
            ),
            UserLimitReachedError,
        ],
        [
            ConnectFourLobby(
                id=_LOBBY_ID,
                name=_NAME,
                users={_OTHER_USER_ID: UserRole.ADMIN},
                admin_role_transfer_queue=[],
                password=_PASSWORD,
                time_for_each_player=_TIME_FOR_EACH_PLAYER,
            ),
            None,
            JoinLobbyCommand(
                lobby_id=_LOBBY_ID,
                password=None,
            ),
            PasswordRequiredError,
        ],
        [
            ConnectFourLobby(
                id=_LOBBY_ID,
                name=_NAME,
                users={_OTHER_USER_ID: UserRole.ADMIN},
                admin_role_transfer_queue=[],
                password=_PASSWORD,
                time_for_each_player=_TIME_FOR_EACH_PLAYER,
            ),
            None,
            JoinLobbyCommand(
                lobby_id=_LOBBY_ID,
                password="Incorrect password",
            ),
            IncorrectPasswordError,
        ],
    ],
)
async def test_join_lobby_processor_errors(
    lobby: Lobby | None,
    game: Game | None,
    command: JoinLobbyCommand,
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
    centrifugo_client = FakeCentrifugoClient()

    command_processor = JoinLobbyProcessor(
        join_lobby=JoinLobby(),
        lobby_gateway=lobby_gateway,
        game_gateway=game_gateway,
        event_publisher=event_publisher,
        centrifugo_client=centrifugo_client,
        transaction_manager=AsyncMock(),
        identity_provider=FakeIdentityProvider(_CURRENT_USER_ID),
    )

    with pytest.raises(expected_error):
        await command_processor.process(command)

    assert not event_publisher.events
    assert not centrifugo_client.publications
