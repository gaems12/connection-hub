# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from datetime import datetime, timedelta, timezone
from typing import Final

from uuid_extensions import uuid7

from connection_hub.domain.identitifiers import (
    PlayerStateId,
    GameId,
    UserId,
)
from connection_hub.domain.constants import UserRole, PlayerStatus
from connection_hub.domain.models import (
    ConnectFourLobby,
    Lobby,
    PlayerState,
    ConnectFourGame,
    Game,
)
from connection_hub.domain.exceptions import UserIsNotAdminError


_TIME_FOR_RECONNECT: Final = timedelta(seconds=40)


class CreateGame:
    def __call__(
        self,
        *,
        lobby: Lobby,
        current_user_id: UserId,
    ) -> Game:
        if lobby.users[current_user_id] != UserRole.ADMIN:
            raise UserIsNotAdminError()

        players = {
            player_id: PlayerState(
                id=PlayerStateId(uuid7()),
                status=PlayerStatus.CONNECTED,
                time_left=_TIME_FOR_RECONNECT,
            )
            for player_id in lobby.users
        }

        if isinstance(lobby, ConnectFourLobby):
            return ConnectFourGame(
                id=GameId(uuid7()),
                players=players,
                created_at=datetime.now(timezone.utc),
                time_for_each_player=lobby.time_for_each_player,
            )
