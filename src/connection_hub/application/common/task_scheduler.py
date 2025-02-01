# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

__all__ = (
    "DisqualifyPlayerTask",
    "Task",
    "TaskScheduler",
)

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Protocol
from uuid import UUID

from connection_hub.domain import GameId, PlayerStateId


@dataclass(frozen=True, slots=True, kw_only=True)
class BaseTask:
    id: UUID
    execute_at: datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class DisqualifyPlayerTask(BaseTask):
    game_id: GameId
    player_id: UUID
    player_state_id: PlayerStateId


type Task = DisqualifyPlayerTask


class TaskScheduler(Protocol):
    async def schedule(self, task: Task) -> None:
        raise NotImplementedError

    async def unschedule_many(self, task_ids: Iterable[UUID]) -> None:
        raise NotImplementedError
