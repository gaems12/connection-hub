# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from dataclasses import dataclass

from connection_hub.domain import GameId
from connection_hub.application.common import (
    GameGateway,
    TaskScheduler,
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
            game_id=command.game_id,
            acquire=True,
        )
        if not game:
            raise GameDoesNotExistError()

        await self._game_gateway.delete(game)

        task_ids = [player_state.id for player_state in game.players.values()]
        await self._task_scheduler.unschedule_many(task_ids)

        await self._transaction_manager.commit()
