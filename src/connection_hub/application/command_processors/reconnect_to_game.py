# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from connection_hub.domain import (
    UserId,
    ConnectFourGame,
    Game,
    ReconnectToGame,
)
from connection_hub.application.common import (
    GameGateway,
    ConnectFourGamePlayerReconnectedEvent,
    EventPublisher,
    TaskScheduler,
    TransactionManager,
    IdentityProvider,
    UserNotInGameError,
)


class ReconnectToGameProcessor:
    __slots__ = (
        "_reconnect_to_game",
        "_game_gateway",
        "_event_publisher",
        "_task_scheduler",
        "_transaction_manager",
        "_identity_provider",
    )

    def __init__(
        self,
        reconnect_to_game: ReconnectToGame,
        game_gateway: GameGateway,
        event_publisher: EventPublisher,
        task_scheduler: TaskScheduler,
        transaction_manager: TransactionManager,
        identity_provider: IdentityProvider,
    ):
        self._reconnect_to_game = reconnect_to_game
        self._game_gateway = game_gateway
        self._event_publisher = event_publisher
        self._task_scheduler = task_scheduler
        self._transaction_manager = transaction_manager
        self._identity_provider = identity_provider

    async def process(self) -> None:
        current_user_id = await self._identity_provider.user_id()

        game = await self._game_gateway.by_player_id(
            player_id=current_user_id,
            acquire=True,
        )
        if not game:
            raise UserNotInGameError()

        self._reconnect_to_game(
            game=game,
            current_user_id=current_user_id,
        )
        await self._game_gateway.update(game)

        current_player_state = game.players[current_user_id]
        await self._task_scheduler.unschedule(current_player_state.id)

        await self._publish_event(
            game=game,
            current_player_id=current_user_id,
        )

        await self._transaction_manager.commit()

    async def _publish_event(
        self,
        *,
        game: Game,
        current_player_id: UserId,
    ) -> None:
        if isinstance(game, ConnectFourGame):
            event = ConnectFourGamePlayerReconnectedEvent(
                game_id=game.id,
                player_id=current_player_id,
            )

        await self._event_publisher.publish(event)
