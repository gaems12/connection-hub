# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from typing import Final

from connection_hub.domain.identitifiers import UserId
from connection_hub.domain.constants import UserRole
from connection_hub.domain.models import ConnectFourLobby, Lobby
from connection_hub.domain.exceptions import (
    UserLimitReachedError,
    PasswordRequiredError,
    IncorrectPasswordError,
)


_LOBBY_TO_MAX_PLAYERS_MAP: Final = {
    ConnectFourLobby: 2,
}


class JoinLobby:
    def __call__(
        self,
        *,
        lobby: Lobby,
        current_user_id: UserId,
        password: str | None,
    ) -> None:
        if current_user_id in lobby.users:
            raise Exception(
                "JoinLobby. Cannot join lobby: user already in the lobby.",
            )

        max_players = _LOBBY_TO_MAX_PLAYERS_MAP[type(lobby)]
        if len(lobby.users) == max_players:
            raise UserLimitReachedError()

        if lobby.password and not password:
            raise PasswordRequiredError()

        if lobby.password != password:
            raise IncorrectPasswordError()

        lobby.users[current_user_id] = UserRole.REGULAR_MEMBER
        lobby.admin_role_transfer_queue.append(current_user_id)
