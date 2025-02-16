# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from dataclasses import dataclass
from datetime import datetime, timedelta

from connection_hub.domain.identitifiers import GameId, UserId
from .player_state import PlayerState


@dataclass(slots=True, kw_only=True)
class BaseGame:
    id: GameId
    players: dict[UserId, PlayerState]
    created_at: datetime


@dataclass(slots=True, kw_only=True)
class ConnectFourGame(BaseGame):
    time_for_each_player: timedelta


type Game = ConnectFourGame
