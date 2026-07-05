# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = (
    "LobbyCreatedEvent",
    "UserJoinedLobbyEvent",
    "UserLeftLobbyEvent",
    "UserRemovedFromLobbyEvent",
    "UserKickedFromLobbyEvent",
    "ConnectFourGamePlayer",
    "ConnectFourGameCreatedEvent",
    "ConnectFourGamePlayerDisconnectedEvent",
    "ConnectFourGamePlayerReconnectedEvent",
    "ConnectFourGamePlayerDisqualifiedEvent",
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
    has_password: bool
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
class UserRemovedFromLobbyEvent:
    lobby_id: LobbyId
    user_id: UserId
    new_admin_id: UserId | None


@dataclass(frozen=True, slots=True, kw_only=True)
class UserKickedFromLobbyEvent:
    lobby_id: LobbyId
    user_id: UserId


@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectFourGamePlayer:
    id: UserId
    time: timedelta
    communication_type: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectFourGameCreatedEvent:
    game_id: GameId
    lobby_id: LobbyId
    first_player: ConnectFourGamePlayer
    second_player: ConnectFourGamePlayer
    created_at: datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectFourGamePlayerDisconnectedEvent:
    game_id: GameId
    player_id: UserId


@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectFourGamePlayerReconnectedEvent:
    game_id: GameId
    player_id: UserId


@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectFourGamePlayerDisqualifiedEvent:
    game_id: GameId
    player_id: UserId


type Event = (
    LobbyCreatedEvent
    | UserJoinedLobbyEvent
    | UserLeftLobbyEvent
    | UserRemovedFromLobbyEvent
    | UserKickedFromLobbyEvent
    | ConnectFourGameCreatedEvent
    | ConnectFourGamePlayerDisconnectedEvent
    | ConnectFourGamePlayerReconnectedEvent
    | ConnectFourGamePlayerDisqualifiedEvent
)


class EventPublisher(Protocol):
    async def publish(self, event: Event) -> None:
        raise NotImplementedError
