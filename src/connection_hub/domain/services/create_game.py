# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from datetime import datetime, timezone

from uuid_extensions import uuid7

from connection_hub.domain.identitifiers import GameId, UserId
from connection_hub.domain.constants import UserRole
from connection_hub.domain.models import (
    FourInARowLobby,
    Lobby,
    FourInARowGame,
    Game,
)
from connection_hub.domain.exceptions import UserIsNotAdminError


class CreateGame:
    def __call__(
        self,
        *,
        lobby: Lobby,
        current_user_id: UserId,
    ) -> Game:
        if lobby.users[current_user_id] != UserRole.ADMIN:
            raise UserIsNotAdminError()

        if isinstance(lobby, FourInARowLobby):
            return FourInARowGame(
                id=GameId(uuid7()),
                players=list(lobby.users.keys()),
                created_at=datetime.now(timezone.utc),
                time_for_each_player=lobby.time_for_each_player,
            )
