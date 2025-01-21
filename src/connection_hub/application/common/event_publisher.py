# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

__all__ = (
    "LobbyCreatedEvent",
    "Event",
    "EventPublisher",
)

from dataclasses import dataclass
from typing import Protocol

from connection_hub.domain import LobbyId, UserId, RuleSet


@dataclass(frozen=True, slots=True)
class LobbyCreatedEvent:
    id: LobbyId
    name: str
    admin_id: UserId
    rule_set: RuleSet


type Event = LobbyCreatedEvent


class EventPublisher(Protocol):
    async def publish(self, event: Event) -> None:
        raise NotImplementedError
