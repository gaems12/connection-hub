# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

__all__ = (
    "GameType",
    "GAME_TO_GAME_TYPE_MAP",
)

from typing import Final
from enum import StrEnum

from connection_hub.domain import ConnectFourGame


class GameType(StrEnum):
    CONNECT_FOUR = "connect_four"


GAME_TO_GAME_TYPE_MAP: Final = {
    ConnectFourGame: GameType.CONNECT_FOUR,
}
