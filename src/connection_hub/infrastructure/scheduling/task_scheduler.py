# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = ("TaskiqTaskScheduler",)

import logging
from typing import Iterable
from typing_extensions import Final

from taskiq import ScheduledTask
from taskiq_redis import RedisScheduleSource

from connection_hub.application import (
    TryToDisqualifyPlayerCommand,
    RemoveFromLobbyCommand,
    DisconnectFromGameCommand,
    RemoveFromLobbyTask,
    DisconnectFromGameTask,
    TryToDisqualifyPlayerTask,
    Task,
    TaskScheduler,
)
from connection_hub.infrastructure.operation_id import OperationId


_logger: Final = logging.getLogger(__name__)


class TaskiqTaskScheduler(TaskScheduler):
    __slots__ = ("_schedule_source", "_operation_id")

    def __init__(
        self,
        schedule_source: RedisScheduleSource,
        operation_id: OperationId,
    ):
        self._schedule_source = schedule_source
        self._operation_id = operation_id

    async def schedule(self, task: Task) -> None:
        if isinstance(task, TryToDisqualifyPlayerTask):
            await self._schedule_try_to_disqualify_player(task)

        elif isinstance(task, RemoveFromLobbyTask):
            await self._schedule_remove_from_lobby(task)

        elif isinstance(task, DisconnectFromGameTask):
            await self._schedule_disconnect_from_game(task)

    async def schedule_many(self, tasks: Iterable[Task]) -> None:
        for task in tasks:
            await self.schedule(task)

    async def unschedule(self, task_id: str) -> None:
        await self._schedule_source.delete_schedule(task_id)

    async def unschedule_many(self, task_ids: Iterable[str]) -> None:
        for task_id in task_ids:
            await self.unschedule(task_id)

    async def _schedule_try_to_disqualify_player(
        self,
        task: TryToDisqualifyPlayerTask,
    ) -> None:
        command = TryToDisqualifyPlayerCommand(
            game_id=task.game_id,
            player_id=task.player_id,
            player_state_id=task.player_state_id,
        )
        schedule = ScheduledTask(
            task_name="try_to_disqualify_player",
            labels={},
            args=[self._operation_id],
            kwargs={"command": command},
            schedule_id=task.id,
            time=task.execute_at,
        )

        _logger.debug(
            {
                "message": "About to schedule a task.",
                "task": schedule.model_dump(mode="json"),
            },
        )

        await self._schedule_source.add_schedule(schedule)

    async def _schedule_remove_from_lobby(
        self,
        task: RemoveFromLobbyTask,
    ) -> None:
        command = RemoveFromLobbyCommand(
            lobby_id=task.lobby_id,
            user_id=task.user_id,
        )
        schedule = ScheduledTask(
            task_name="remove_from_lobby",
            labels={},
            args=[self._operation_id],
            kwargs={"command": command},
            schedule_id=task.id,
            time=task.execute_at,
        )

        _logger.debug(
            {
                "message": "About to schedule a task.",
                "task": schedule.model_dump(mode="json"),
            },
        )

        await self._schedule_source.add_schedule(schedule)

    async def _schedule_disconnect_from_game(
        self,
        task: DisconnectFromGameTask,
    ) -> None:
        command = DisconnectFromGameCommand(
            game_id=task.game_id,
            user_id=task.player_id,
        )
        schedule = ScheduledTask(
            task_name="disconnect_from_game",
            labels={},
            args=[self._operation_id],
            kwargs={"command": command},
            schedule_id=task.id,
            time=task.execute_at,
        )

        _logger.debug(
            {
                "message": "About to schedule a task.",
                "task": schedule.model_dump(mode="json"),
            },
        )

        await self._schedule_source.add_schedule(schedule)
