# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = ("PlayerStatus",)

from enum import StrEnum


class PlayerStatus(StrEnum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
