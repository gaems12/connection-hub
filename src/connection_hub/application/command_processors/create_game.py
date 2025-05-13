# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = ("CreateGameCommand", "CreateGameProcessor")

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from connection_hub.domain import (
    LobbyId,
    ConnectFourGame,
    Game,
    CreateGame,
)
from connection_hub.application.common import (
    LobbyGateway,
    GameGateway,
    ConnectFourGameCreatedEvent,
    EventPublisher,
    remove_from_lobby_task_id_factory,
    DisconnectFromGameTask,
    disconnect_from_game_task_id_factory,
    TaskScheduler,
    TransactionManager,
    IdentityProvider,
    LobbyDoesNotExistError,
    CurrentUserNotInLobbyError,
)


@dataclass(frozen=True, slots=True)
class CreateGameCommand:
    lobby_id: LobbyId


class CreateGameProcessor:
    __slots__ = (
        "_create_game",
        "_lobby_gateway",
        "_game_gateway",
        "_event_publisher",
        "_task_scheduler",
        "_transaction_manager",
        "_identity_provider",
    )

    def __init__(
        self,
        create_game: CreateGame,
        lobby_gateway: LobbyGateway,
        game_gateway: GameGateway,
        event_publisher: EventPublisher,
        task_scheduler: TaskScheduler,
        transaction_manager: TransactionManager,
        identity_provider: IdentityProvider,
    ):
        self._create_game = create_game
        self._lobby_gateway = lobby_gateway
        self._game_gateway = game_gateway
        self._event_publisher = event_publisher
        self._task_scheduler = task_scheduler
        self._transaction_manager = transaction_manager
        self._identity_provider = identity_provider

    async def process(self, command: CreateGameCommand) -> None:
        current_user_id = await self._identity_provider.user_id()

        lobby = await self._lobby_gateway.by_id(
            lobby_id=command.lobby_id,
            acquire=True,
        )
        if not lobby:
            raise LobbyDoesNotExistError()

        if current_user_id not in lobby.users:
            raise CurrentUserNotInLobbyError()

        new_game = self._create_game(
            lobby=lobby,
            current_user_id=current_user_id,
        )
        await self._game_gateway.save(new_game)

        execute_tasks_at = datetime.now(timezone.utc) + timedelta(
            seconds=15,
        )

        ids_of_tasks_to_unchedule = []
        tasks_to_schedule = []
        for user_id in new_game.players:
            id_of_task_to_unschedule = remove_from_lobby_task_id_factory(
                lobby_id=lobby.id,
                user_id=user_id,
            )
            ids_of_tasks_to_unchedule.append(id_of_task_to_unschedule)

            task_id = disconnect_from_game_task_id_factory(
                game_id=new_game.id,
                player_id=user_id,
            )
            task = DisconnectFromGameTask(
                id=task_id,
                execute_at=execute_tasks_at,
                game_id=new_game.id,
                player_id=user_id,
            )
            tasks_to_schedule.append(task)

        await self._task_scheduler.unschedule_many(ids_of_tasks_to_unchedule)
        await self._task_scheduler.schedule_many(tasks_to_schedule)

        await self._publish_event(lobby_id=lobby.id, game=new_game)

        await self._transaction_manager.commit()

    async def _publish_event(
        self,
        *,
        lobby_id: LobbyId,
        game: Game,
    ) -> None:
        if isinstance(game, ConnectFourGame):
            player_ids = list(game.players.keys())
            event = ConnectFourGameCreatedEvent(
                game_id=game.id,
                lobby_id=lobby_id,
                first_player_id=player_ids[0],
                second_player_id=player_ids[1],
                time_for_each_player=game.time_for_each_player,
                created_at=game.created_at,
            )

        await self._event_publisher.publish(event)
