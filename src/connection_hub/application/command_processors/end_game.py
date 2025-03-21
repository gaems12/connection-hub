# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from dataclasses import dataclass

from connection_hub.domain import GameId
from connection_hub.application.common import (
    GameGateway,
    TaskScheduler,
    force_disconnect_from_game_task_id_factory,
    try_to_disqualify_player_task_id_factory,
    TransactionManager,
    GameDoesNotExistError,
)


@dataclass(frozen=True, slots=True)
class EndGameCommand:
    game_id: GameId


class EndGameProcessor:
    __slots__ = (
        "_game_gateway",
        "_task_scheduler",
        "_transaction_manager",
    )

    def __init__(
        self,
        game_gateway: GameGateway,
        task_scheduler: TaskScheduler,
        transaction_manager: TransactionManager,
    ):
        self._game_gateway = game_gateway
        self._task_scheduler = task_scheduler
        self._transaction_manager = transaction_manager

    async def process(self, command: EndGameCommand) -> None:
        game = await self._game_gateway.by_id(
            id=command.game_id,
            acquire=True,
        )
        if not game:
            raise GameDoesNotExistError()

        await self._game_gateway.delete(game)

        task_ids = []
        for player_id, player_state in game.players.items():
            task_id = force_disconnect_from_game_task_id_factory(
                game_id=game.id,
                player_id=player_id,
            )
            task_ids.append(task_id)

            task_id = try_to_disqualify_player_task_id_factory(
                player_state_id=player_state.id,
            )
            task_ids.append(task_id)

        await self._task_scheduler.unschedule_many(task_ids)

        await self._transaction_manager.commit()
