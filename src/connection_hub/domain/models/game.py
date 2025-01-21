# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from dataclasses import dataclass

from connection_hub.domain.identitifiers import GameId, UserId


@dataclass(slots=True, kw_only=True)
class BaseGame:
    id: GameId
    players: list[UserId]


@dataclass(slots=True, kw_only=True)
class FourInARowGame(BaseGame): ...


type Game = FourInARowGame
