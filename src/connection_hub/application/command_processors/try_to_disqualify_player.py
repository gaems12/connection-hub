# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from dataclasses import dataclass

from connection_hub.domain import (
    GameId,
    UserId,
    PlayerStateId,
    TryToDisqualifyPlayer,
)
from connection_hub.application.common import (
    GAME_TO_GAME_TYPE_MAP,
    GameGateway,
    PlayerDisqualifiedEvent,
    EventPublisher,
    TaskScheduler,
    TransactionManager,
    GameDoesNotExistError,
    UserNotInGameError,
)


@dataclass(frozen=True, slots=True)
class TryToDisqualifyPlayerCommand:
    game_id: GameId
    player_id: UserId
    player_state_id: PlayerStateId


class TryToDisqualifyPlayerProcessor:
    __slots__ = (
        "_try_to_disqualify_player",
        "_game_gateway",
        "_event_publisher",
        "_task_scheduler",
        "_transaction_manager",
    )

    def __init__(
        self,
        try_to_disqualify_player: TryToDisqualifyPlayer,
        game_gateway: GameGateway,
        event_publisher: EventPublisher,
        task_scheduler: TaskScheduler,
        transaction_manager: TransactionManager,
    ):
        self._try_to_disqualify_player = try_to_disqualify_player
        self._game_gateway = game_gateway
        self._event_publisher = event_publisher
        self._task_scheduler = task_scheduler
        self._transaction_manager = transaction_manager

    async def process(self, command: TryToDisqualifyPlayerCommand) -> None:
        game = await self._game_gateway.by_id(
            game_id=command.game_id,
            acquire=True,
        )
        if not game:
            raise GameDoesNotExistError()

        if command.player_id not in game.players:
            raise UserNotInGameError()

        player_is_disqualified, game_is_ended = self._try_to_disqualify_player(
            game=game,
            player_id=command.player_id,
            player_state_id=command.player_state_id,
        )
        if not player_is_disqualified:
            return

        if game_is_ended:
            player_state_ids = map(
                lambda player_state: player_state.id,
                game.players.values(),
            )
            await self._task_scheduler.unschedule_many(player_state_ids)

            await self._game_gateway.delete(game)
        else:
            await self._game_gateway.update(game)

        event = PlayerDisqualifiedEvent(
            game_id=command.game_id,
            game_type=GAME_TO_GAME_TYPE_MAP[type(game)],
            player_id=command.player_id,
        )
        await self._event_publisher.publish(event)

        await self._transaction_manager.commit()
