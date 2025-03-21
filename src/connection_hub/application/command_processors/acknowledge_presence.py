# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from datetime import datetime, timedelta, timezone

from connection_hub.application.common import (
    LobbyGateway,
    GameGateway,
    ForceLeaveLobbyTask,
    force_leave_lobby_task_id_factory,
    ForceDisconnectFromGameTask,
    force_disconnect_from_game_task_id_factory,
    TaskScheduler,
    IdentityProvider,
)


class AcknowledgePresenceProcessor:
    __slots__ = (
        "_lobby_gateway",
        "_game_gateway",
        "_task_scheduler",
        "_identity_provider",
    )

    def __init__(
        self,
        lobby_gateway: LobbyGateway,
        game_gateway: GameGateway,
        task_scheduler: TaskScheduler,
        identity_provider: IdentityProvider,
    ):
        self._lobby_gateway = lobby_gateway
        self._game_gateway = game_gateway
        self._task_scheduler = task_scheduler
        self._identity_provider = identity_provider

    async def process(self) -> None:
        task: ForceLeaveLobbyTask | ForceDisconnectFromGameTask

        current_user_id = await self._identity_provider.user_id()

        lobby = await self._lobby_gateway.by_user_id(
            user_id=current_user_id,
        )
        if lobby:
            task_id = force_leave_lobby_task_id_factory(
                lobby_id=lobby.id,
                user_id=current_user_id,
            )
            execute_task_at = datetime.now(timezone.utc) + timedelta(
                seconds=15,
            )
            task = ForceLeaveLobbyTask(
                id=task_id,
                execute_at=execute_task_at,
                lobby_id=lobby.id,
                user_id=current_user_id,
            )
            await self._task_scheduler.schedule(task)

            return

        game = await self._game_gateway.by_player_id(
            player_id=current_user_id,
        )
        if game:
            task_id = force_disconnect_from_game_task_id_factory(
                game_id=game.id,
                player_id=current_user_id,
            )
            execute_task_at = datetime.now(timezone.utc) + timedelta(
                seconds=15,
            )
            task = ForceDisconnectFromGameTask(
                id=task_id,
                execute_at=execute_task_at,
                game_id=game.id,
                player_id=current_user_id,
            )
            await self._task_scheduler.schedule(task)

            return
