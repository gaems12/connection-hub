# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = ("PlayerState",)

from dataclasses import dataclass
from datetime import timedelta

from connection_hub.domain.identitifiers import PlayerStateId
from connection_hub.domain.constants import PlayerStatus


@dataclass(slots=True, kw_only=True)
class PlayerState:
    id: PlayerStateId
    status: PlayerStatus
    time_left: timedelta
