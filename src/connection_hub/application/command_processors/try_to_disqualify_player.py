# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = ("TryToDisqualifyPlayerCommand", "TryToDisqualifyPlayerProcessor")

from dataclasses import dataclass

from connection_hub.domain import (
    GameId,
    UserId,
    PlayerStateId,
    ConnectFourGame,
    Game,
    TryToDisqualifyPlayer,
)
from connection_hub.application.common import (
    GameGateway,
    ConnectFourGamePlayerDisqualifiedEvent,
    EventPublisher,
    TaskScheduler,
    disconnect_from_game_task_id_factory,
    try_to_disqualify_player_task_id_factory,
    CentrifugoClient,
    centrifugo_game_channel_factory,
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
        "_centrifugo_client",
        "_transaction_manager",
    )

    def __init__(
        self,
        try_to_disqualify_player: TryToDisqualifyPlayer,
        game_gateway: GameGateway,
        event_publisher: EventPublisher,
        task_scheduler: TaskScheduler,
        centrifugo_client: CentrifugoClient,
        transaction_manager: TransactionManager,
    ):
        self._try_to_disqualify_player = try_to_disqualify_player
        self._game_gateway = game_gateway
        self._event_publisher = event_publisher
        self._task_scheduler = task_scheduler
        self._centrifugo_client = centrifugo_client
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
            user_id=command.player_id,
            player_state_id=command.player_state_id,
        )
        if not player_is_disqualified:
            return

        if game_is_ended:
            task_ids = []
            for player_id, player_state in game.players.items():
                task_id = disconnect_from_game_task_id_factory(
                    game_id=game.id,
                    player_id=player_id,
                )
                task_ids.append(task_id)

                task_id = try_to_disqualify_player_task_id_factory(
                    player_state_id=player_state.id,
                )
                task_ids.append(task_id)

            await self._task_scheduler.unschedule_many(task_ids)

            await self._game_gateway.delete(game)
        else:
            await self._game_gateway.update(game)

        await self._publish_event(game=game, player_id=command.player_id)

        centrifugo_publication = {
            "type": "player_disqualified",
            "player_id": command.player_id.hex,
        }
        await self._centrifugo_client.publish(
            channel=centrifugo_game_channel_factory(game.id),
            data=centrifugo_publication,  # type: ignore[arg-type]
        )

        await self._transaction_manager.commit()

    async def _publish_event(
        self,
        *,
        game: Game,
        player_id: UserId,
    ) -> None:
        if isinstance(game, ConnectFourGame):
            event = ConnectFourGamePlayerDisqualifiedEvent(
                game_id=game.id,
                player_id=player_id,
            )

        await self._event_publisher.publish(event)
