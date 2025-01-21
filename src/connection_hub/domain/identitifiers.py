# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

__all__ = ("LobbyId", "GameId", "UserId")

from typing import NewType
from uuid import UUID


LobbyId = NewType("LobbyId", UUID)
GameId = NewType("GameId", UUID)
UserId = NewType("UserId", UUID)
