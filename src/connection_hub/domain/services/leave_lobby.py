# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from connection_hub.domain.identitifiers import UserId
from connection_hub.domain.constants import UserRole
from connection_hub.domain.models import Lobby


class LeaveLobby:
    def __call__(
        self,
        *,
        lobby: Lobby,
        current_user_id: UserId,
    ) -> UserId | None:
        if current_user_id not in lobby.users:
            raise Exception(
                "LeaveLobby. Cannot leave lobby: user is not in the lobby.",
            )

        current_user_role = lobby.users.pop(current_user_id)
        no_users_left = not lobby.users

        if current_user_role != UserRole.ADMIN or no_users_left:
            return None

        next_admin = lobby.admin_role_transfer_queue.pop(0)
        lobby.users[next_admin] = UserRole.ADMIN

        return next_admin
