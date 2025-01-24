# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from dataclasses import dataclass
from datetime import datetime, timedelta

from connection_hub.domain.identitifiers import GameId, UserId


@dataclass(slots=True, kw_only=True)
class BaseGame:
    id: GameId
    players: list[UserId]
    created_at: datetime


@dataclass(slots=True, kw_only=True)
class FourInARowGame(BaseGame):
    time_for_each_player: timedelta


type Game = FourInARowGame
