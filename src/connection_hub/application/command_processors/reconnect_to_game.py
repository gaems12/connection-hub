# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from connection_hub.domain import ReconnectToGame
from connection_hub.application.common import (
    GAME_TO_GAME_TYPE_MAP,
    GameGateway,
    PlayerReconnectedEvent,
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

        event = PlayerReconnectedEvent(
            game_id=game.id,
            game_type=GAME_TO_GAME_TYPE_MAP[type(game)],
            player_id=current_user_id,
        )
        await self._event_publisher.publish(event)

        await self._transaction_manager.commit()
