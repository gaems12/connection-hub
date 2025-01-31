# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

__all__ = ("GAME_TO_GAME_TYPE_MAP",)

from typing import Final

from connection_hub.domain import FourInARowGame
from .event_publisher import GameType


GAME_TO_GAME_TYPE_MAP: Final = {
    FourInARowGame: GameType.FOUR_IN_A_ROW,
}
