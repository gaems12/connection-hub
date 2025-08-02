# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = ("StartGameCommand", "StartGameProcessor")

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from connection_hub.domain import GameId, LobbyId
from connection_hub.application.common import (
    LobbyGateway,
    GameGateway,
    remove_from_lobby_task_id_factory,
    disconnect_from_game_task_id_factory,
    DisconnectFromGameTask,
    TaskScheduler,
    Serializable,
    CENTRIFUGO_LOBBY_BROWSER_CHANNEL,
    CentrifugoClient,
    TransactionManager,
    LobbyDoesNotExistError,
    GameDoesNotExistError,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class StartGameCommand:
    game_id: GameId
    lobby_id: LobbyId


class StartGameProcessor:
    __slots__ = (
        "_lobby_gateway",
        "_game_gateway",
        "_task_scheduler",
        "_centrifugo_client",
        "_transaction_manager",
    )

    def __init__(
        self,
        lobby_gateway: LobbyGateway,
        game_gateway: GameGateway,
        task_scheduler: TaskScheduler,
        centrifugo_client: CentrifugoClient,
        transaction_manager: TransactionManager,
    ):
        self._lobby_gateway = lobby_gateway
        self._game_gateway = game_gateway
        self._task_scheduler = task_scheduler
        self._centrifugo_client = centrifugo_client
        self._transaction_manager = transaction_manager

    async def process(self, command: StartGameCommand) -> None:
        lobby = await self._lobby_gateway.by_id(command.lobby_id)
        if not lobby:
            raise LobbyDoesNotExistError()

        game = await self._game_gateway.by_id(command.game_id)
        if not game:
            raise GameDoesNotExistError()

        await self._lobby_gateway.delete(lobby)

        execute_tasks_at = datetime.now(timezone.utc) + timedelta(
            seconds=15,
        )

        ids_of_tasks_to_unchedule = []
        tasks_to_schedule = []
        for user_id in game.players:
            id_of_task_to_unschedule = remove_from_lobby_task_id_factory(
                lobby_id=lobby.id,
                user_id=user_id,
            )
            ids_of_tasks_to_unchedule.append(id_of_task_to_unschedule)

            task_id = disconnect_from_game_task_id_factory(
                game_id=game.id,
                player_id=user_id,
            )
            task = DisconnectFromGameTask(
                id=task_id,
                execute_at=execute_tasks_at,
                game_id=game.id,
                player_id=user_id,
            )
            tasks_to_schedule.append(task)

        await self._task_scheduler.unschedule_many(ids_of_tasks_to_unchedule)
        await self._task_scheduler.schedule_many(tasks_to_schedule)

        centrifugo_publication: Serializable = {
            "type": "lobby_removed",
            "lobby_id": lobby.id.hex,
        }
        await self._centrifugo_client.publish(
            channel=CENTRIFUGO_LOBBY_BROWSER_CHANNEL,
            data=centrifugo_publication,
        )

        await self._transaction_manager.commit()
