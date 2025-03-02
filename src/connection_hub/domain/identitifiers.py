# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = ("LobbyId", "PlayerStateId", "GameId", "UserId")

from typing import NewType
from uuid import UUID


LobbyId = NewType("LobbyId", UUID)
PlayerStateId = NewType("PlayerStateId", UUID)
GameId = NewType("GameId", UUID)
UserId = NewType("UserId", UUID)
