# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from uuid import UUID
from typing import Iterable

from taskiq import ScheduledTask
from taskiq_redis import RedisScheduleSource

from connection_hub.application import (
    TryToDisqualifyPlayerCommand,
    ForceLeaveLobbyCommand,
    ForceLeaveLobbyTask,
    ForceDisconnectFromGameTask,
    TryToDisqualifyPlayerTask,
    Task,
    TaskScheduler,
)
from connection_hub.infrastructure.operation_id import OperationId


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

        elif isinstance(task, ForceLeaveLobbyTask):
            await self._schedule_force_leave_lobby(task)

        elif isinstance(task, ForceDisconnectFromGameTask):
            await self._schedule_force_disconnect_from_game(task)

    async def unschedule(self, task_id: UUID) -> None:
        await self._schedule_source.delete_schedule(task_id.hex)

    async def unschedule_many(self, task_ids: Iterable[UUID]) -> None:
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
            schedule_id=task.id.hex,
            time=task.execute_at,
        )
        await self._schedule_source.add_schedule(schedule)

    async def _schedule_force_leave_lobby(
        self,
        task: ForceLeaveLobbyTask,
    ) -> None:
        command = ForceLeaveLobbyCommand(
            lobby_id=task.lobby_id,
            user_id=task.user_id,
        )

        schedule = ScheduledTask(
            task_name="force_leave_lobby",
            labels={},
            args=[self._operation_id],
            kwargs={"command": command},
            schedule_id=task.id.hex,
            time=task.execute_at,
        )
        await self._schedule_source.add_schedule(schedule)

    async def _schedule_force_disconnect_from_game(
        self,
        task: ForceDisconnectFromGameTask,
    ) -> None: ...
