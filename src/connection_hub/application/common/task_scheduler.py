# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = (
    "remove_from_lobby_task_id_factory",
    "disconnect_from_game_task_id_factory",
    "try_to_disqualify_player_task_id_factory",
    "RemoveFromLobbyTask",
    "DisconnectFromGameTask",
    "TryToDisqualifyPlayerTask",
    "Task",
    "TaskScheduler",
)

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Protocol

from connection_hub.domain import LobbyId, GameId, UserId, PlayerStateId


def remove_from_lobby_task_id_factory(
    *,
    lobby_id: LobbyId,
    user_id: UserId,
) -> str:
    return f"remove_from_lobby:{lobby_id.hex}:{user_id.hex}"


def disconnect_from_game_task_id_factory(
    *,
    game_id: GameId,
    player_id: UserId,
) -> str:
    return f"disconnect_from_game:{game_id.hex}:{player_id.hex}"


def try_to_disqualify_player_task_id_factory(
    player_state_id: PlayerStateId,
) -> str:
    return f"try_to_disqualify_player:{player_state_id.hex}"


@dataclass(frozen=True, slots=True, kw_only=True)
class BaseTask:
    id: str
    execute_at: datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class RemoveFromLobbyTask(BaseTask):
    lobby_id: LobbyId
    user_id: UserId


@dataclass(frozen=True, slots=True, kw_only=True)
class DisconnectFromGameTask(BaseTask):
    game_id: GameId
    player_id: UserId


@dataclass(frozen=True, slots=True, kw_only=True)
class TryToDisqualifyPlayerTask(BaseTask):
    game_id: GameId
    player_id: UserId
    player_state_id: PlayerStateId


type Task = (
    RemoveFromLobbyTask | DisconnectFromGameTask | TryToDisqualifyPlayerTask
)


class TaskScheduler(Protocol):
    async def schedule(self, task: Task) -> None:
        """
        Schedules a task. If a task with the provided id
        is already scheduled, it will be uncheduled and
        replaced with the provided task.
        """
        raise NotImplementedError

    async def unschedule(self, task_id: str) -> None:
        raise NotImplementedError

    async def unschedule_many(self, task_ids: Iterable[str]) -> None:
        raise NotImplementedError
