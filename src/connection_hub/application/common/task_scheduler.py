# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = (
    "force_leave_lobby_task_id_factory",
    "force_disconnect_from_game_task_id_factory",
    "try_to_disqualify_player_task_id_factory",
    "ForceLeaveLobbyTask",
    "ForceDisconnectFromGameTask",
    "TryToDisqualifyPlayerTask",
    "Task",
    "TaskScheduler",
)

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Protocol

from connection_hub.domain import LobbyId, GameId, UserId, PlayerStateId


def force_leave_lobby_task_id_factory(
    *,
    lobby_id: LobbyId,
    user_id: UserId,
) -> str:
    return f"force_leave_lobby:{lobby_id.hex}:{user_id.hex}"


def force_disconnect_from_game_task_id_factory(
    *,
    game_id: GameId,
    player_id: UserId,
) -> str:
    return f"force_disconnect_from_game:{game_id.hex}:{player_id.hex}"


def try_to_disqualify_player_task_id_factory(
    player_state_id: PlayerStateId,
) -> str:
    return f"try_to_disqualify_player:{player_state_id.hex}"


@dataclass(frozen=True, slots=True, kw_only=True)
class BaseTask:
    id: str
    execute_at: datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class ForceLeaveLobbyTask(BaseTask):
    lobby_id: LobbyId
    user_id: UserId


@dataclass(frozen=True, slots=True, kw_only=True)
class ForceDisconnectFromGameTask(BaseTask):
    game_id: GameId
    player_id: UserId


@dataclass(frozen=True, slots=True, kw_only=True)
class TryToDisqualifyPlayerTask(BaseTask):
    game_id: GameId
    player_id: UserId
    player_state_id: PlayerStateId


type Task = (
    ForceLeaveLobbyTask
    | ForceDisconnectFromGameTask
    | TryToDisqualifyPlayerTask
)


class TaskScheduler(Protocol):
    async def schedule(self, task: Task) -> None:
        raise NotImplementedError

    async def unschedule(self, task_id: str) -> None:
        raise NotImplementedError

    async def unschedule_many(self, task_ids: Iterable[str]) -> None:
        raise NotImplementedError
