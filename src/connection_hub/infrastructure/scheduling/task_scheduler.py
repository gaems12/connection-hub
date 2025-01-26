# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from uuid import UUID

from taskiq import ScheduledTask
from taskiq_redis import RedisScheduleSource

from connection_hub.application import (
    DisqualifyPlayerTask,
    Task,
    TaskScheduler,
)


class TaskiqTaskScheduler(TaskScheduler):
    __slots__ = ("schedule_source",)

    def __init__(self, schedule_source: RedisScheduleSource):
        self._schedule_source = schedule_source

    async def schedule(self, task: Task) -> None:
        if isinstance(task, DisqualifyPlayerTask):
            await self._schedule_disqualify_player(task)

    async def _schedule_disqualify_player(
        self,
        task: DisqualifyPlayerTask,
    ) -> None:
        schedule = ScheduledTask(
            task_name="disqualify_player",
            labels={},
            args=[],
            kwargs={
                "player_id": task.player_id,
                "player_state_id": task.player_state_id,
            },
            schedule_id=task.id.hex,
            time=task.execute_at,
        )
        await self._schedule_source.add_schedule(schedule)

    async def unschedule(self, task_id: UUID) -> None:
        await self._schedule_source.delete_schedule(task_id.hex)
