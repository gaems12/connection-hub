# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

__all__ = ("LobbyId", "PlayerStateId", "GameId", "UserId")

from typing import NewType
from uuid import UUID


LobbyId = NewType("LobbyId", UUID)
PlayerStateId = NewType("PlayerStateId", UUID)
GameId = NewType("GameId", UUID)
UserId = NewType("UserId", UUID)
