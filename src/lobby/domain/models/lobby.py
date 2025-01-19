# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from dataclasses import dataclass
from datetime import timedelta

from lobby.domain.identitifiers import LobbyId, UserId
from lobby.domain.constants import UserRole


@dataclass(slots=True, kw_only=True)
class BaseLobby:
    id: LobbyId
    name: str
    users: dict[UserId, UserRole]
    password: str | None


@dataclass(slots=True, kw_only=True)
class FourInARowLobby(BaseLobby):
    time_for_each_player: timedelta


type Lobby = FourInARowLobby
