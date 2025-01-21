# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from typing import Final

from connection_hub.domain.identitifiers import UserId
from connection_hub.domain.constants import UserRole
from connection_hub.domain.models import Lobby, FourInARowGame
from connection_hub.domain.exceptions import (
    UserLimitReachedError,
    PasswordRequiredError,
    IncorrectPasswordError,
)


_GAME_TO_MAX_PLAYERS_MAP: Final = {
    FourInARowGame: 2,
}


class JoinLobby:
    def __call__(
        self,
        *,
        lobby: Lobby,
        current_user_id: UserId,
        password: str | None,
    ) -> None:
        max_players = _GAME_TO_MAX_PLAYERS_MAP[type(lobby)]
        if len(lobby.users) == max_players:
            raise UserLimitReachedError()

        if lobby.password and not password:
            raise PasswordRequiredError()

        if lobby.password != password:
            raise IncorrectPasswordError()

        lobby.users[current_user_id] = UserRole.REGULAR_MEMBER
