# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = ("CreateLobby",)

from uuid_extensions import uuid7

from connection_hub.domain.identitifiers import LobbyId, UserId
from connection_hub.domain.constants import UserRole
from connection_hub.domain.models import (
    ConnectFourRuleSet,
    RuleSet,
    ConnectFourLobby,
    Lobby,
)


class CreateLobby:
    def __call__(
        self,
        *,
        name: str,
        current_user_id: UserId,
        rule_set: RuleSet,
        password: str | None = None,
    ) -> Lobby:
        if isinstance(rule_set, ConnectFourRuleSet):
            return ConnectFourLobby(
                id=LobbyId(uuid7()),
                name=name,
                users={current_user_id: UserRole.ADMIN},
                admin_role_transfer_queue=[],
                password=password,
                time_for_each_player=rule_set.time_for_each_player,
            )
