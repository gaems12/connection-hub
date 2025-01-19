# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from uuid_extensions import uuid7

from lobby.domain.identitifiers import LobbyId, UserId
from lobby.domain.constants import UserRole
from lobby.domain.models import (
    FourInARowRuleSet,
    RuleSet,
    FourInARowLobby,
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
        if isinstance(rule_set, FourInARowRuleSet):
            return FourInARowLobby(
                id=LobbyId(uuid7()),
                name=name,
                users={current_user_id: UserRole.ADMIN},
                password=password,
                time_for_each_player=rule_set.time_for_each_player,
            )
