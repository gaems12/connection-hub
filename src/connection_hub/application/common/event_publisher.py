# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

__all__ = (
    "LobbyCreatedEvent",
    "UserJoinedLobbyEvent",
    "UserLeftLobbyEvent",
    "FourInARowGameCreatedEvent",
    "Event",
    "EventPublisher",
)

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol

from connection_hub.domain import LobbyId, GameId, UserId, RuleSet


@dataclass(frozen=True, slots=True, kw_only=True)
class LobbyCreatedEvent:
    lobby_id: LobbyId
    name: str
    admin_id: UserId
    rule_set: RuleSet


@dataclass(frozen=True, slots=True, kw_only=True)
class UserJoinedLobbyEvent:
    lobby_id: LobbyId
    user_id: UserId


@dataclass(frozen=True, slots=True, kw_only=True)
class UserLeftLobbyEvent:
    lobby_id: LobbyId
    user_id: UserId
    new_admin_id: UserId | None


@dataclass(frozen=True, slots=True, kw_only=True)
class FourInARowGameCreatedEvent:
    game_id: GameId
    lobby_id: LobbyId
    first_player_id: UserId
    second_player_id: UserId
    time_for_each_player: timedelta
    created_at: datetime


type Event = (
    LobbyCreatedEvent
    | UserJoinedLobbyEvent
    | UserLeftLobbyEvent
    | FourInARowGameCreatedEvent
)


class EventPublisher(Protocol):
    async def publish(self, event: Event) -> None:
        raise NotImplementedError
