# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from connection_hub.domain.identitifiers import UserId
from connection_hub.domain.models import Lobby


class LeaveLobby:
    def __call__(
        self,
        *,
        lobby: Lobby,
        current_user_id: UserId,
    ) -> None:
        if current_user_id not in lobby.users:
            raise Exception(
                "LeaveLobby. Cannot leave lobby: user is not in the lobby.",
            )

        lobby.users.pop(current_user_id)
