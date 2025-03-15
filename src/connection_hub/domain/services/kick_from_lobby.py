# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from connection_hub.domain.constants import UserRole
from connection_hub.domain.identitifiers import UserId
from connection_hub.domain.models import Lobby
from connection_hub.domain.exceptions import (
    CurrentUserIsNotAdminError,
    CurrentUserIsTryingKickHimselfError,
)


class KickFromLobby:
    def __call__(
        self,
        *,
        lobby: Lobby,
        user_to_kick: UserId,
        current_user_id: UserId,
    ) -> None:
        if lobby.users[current_user_id] != UserRole.ADMIN:
            raise CurrentUserIsNotAdminError()

        if user_to_kick == current_user_id:
            raise CurrentUserIsTryingKickHimselfError()

        lobby.users.pop(user_to_kick)
        lobby.admin_role_transfer_queue.remove(user_to_kick)
