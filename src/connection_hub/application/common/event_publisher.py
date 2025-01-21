# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

__all__ = (
    "LobbyCreatedEvent",
    "UserJoinedLobbyEvent",
    "Event",
    "EventPublisher",
)

from dataclasses import dataclass
from typing import Protocol

from connection_hub.domain import LobbyId, UserId, RuleSet


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


type Event = LobbyCreatedEvent | UserJoinedLobbyEvent


class EventPublisher(Protocol):
    async def publish(self, event: Event) -> None:
        raise NotImplementedError
