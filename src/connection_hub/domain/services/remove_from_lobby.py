# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from connection_hub.domain.identitifiers import UserId
from connection_hub.domain.constants import UserRole
from connection_hub.domain.models import Lobby


class RemoveFromLobby:
    def __call__(
        self,
        *,
        lobby: Lobby,
        user_id: UserId,
    ) -> tuple[bool, UserId | None]:
        """
        Removes user from lobby and manages admin role transfer if
        necessary. Returns two values: whether no users remain in
        the lobby and the id of the next admin if the admin role
        was transferred.
        """
        user_role = lobby.users.pop(user_id)
        no_users_left = not lobby.users
        if no_users_left:
            return True, None

        if user_role != UserRole.ADMIN:
            lobby.admin_role_transfer_queue.remove(user_id)
            return False, None

        next_admin = lobby.admin_role_transfer_queue.pop(0)
        lobby.users[next_admin] = UserRole.ADMIN

        return False, next_admin
