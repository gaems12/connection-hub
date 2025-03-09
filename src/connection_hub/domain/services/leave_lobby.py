# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from connection_hub.domain.identitifiers import UserId
from connection_hub.domain.constants import UserRole
from connection_hub.domain.models import Lobby


class LeaveLobby:
    def __call__(
        self,
        *,
        lobby: Lobby,
        current_user_id: UserId,
    ) -> tuple[bool, UserId | None]:
        """
        Handles a user leaving a lobby and manages admin role
        transfer if necessary. Returns two values: whether no users
        remain in the lobby and the id of the next admin if the admin
        role was transferred.
        """
        if current_user_id not in lobby.users:
            raise Exception(
                "Cannot leave lobby: user is not in the lobby.",
            )

        current_user_role = lobby.users.pop(current_user_id)
        no_users_left = not lobby.users
        if no_users_left:
            return True, None

        if current_user_role != UserRole.ADMIN:
            return False, None

        next_admin = lobby.admin_role_transfer_queue.pop(0)
        lobby.users[next_admin] = UserRole.ADMIN

        return False, next_admin
