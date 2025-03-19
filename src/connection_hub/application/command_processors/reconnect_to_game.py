# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from dataclasses import dataclass

from connection_hub.domain import (
    GameId,
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
    CentrifugoClient,
    centrifugo_game_channel_factory,
    TransactionManager,
    IdentityProvider,
    GameDoesNotExistError,
    CurrentUserNotInGameError,
)


@dataclass(frozen=True, slots=True)
class ReconnectToGameCommand:
    game_id: GameId


class ReconnectToGameProcessor:
    __slots__ = (
        "_reconnect_to_game",
        "_game_gateway",
        "_event_publisher",
        "_task_scheduler",
        "_centrifugo_client",
        "_transaction_manager",
        "_identity_provider",
    )

    def __init__(
        self,
        reconnect_to_game: ReconnectToGame,
        game_gateway: GameGateway,
        event_publisher: EventPublisher,
        task_scheduler: TaskScheduler,
        centrifugo_client: CentrifugoClient,
        transaction_manager: TransactionManager,
        identity_provider: IdentityProvider,
    ):
        self._reconnect_to_game = reconnect_to_game
        self._game_gateway = game_gateway
        self._event_publisher = event_publisher
        self._task_scheduler = task_scheduler
        self._centrifugo_client = centrifugo_client
        self._transaction_manager = transaction_manager
        self._identity_provider = identity_provider

    async def process(self, command: ReconnectToGameCommand) -> None:
        current_user_id = await self._identity_provider.user_id()

        game = await self._game_gateway.by_id(
            id=command.game_id,
            acquire=True,
        )
        if not game:
            raise GameDoesNotExistError()

        if current_user_id not in game.players:
            raise CurrentUserNotInGameError()

        old_current_player_state = game.players[current_user_id]
        old_current_player_state_id = old_current_player_state.id

        self._reconnect_to_game(
            game=game,
            current_user_id=current_user_id,
        )
        await self._game_gateway.update(game)

        await self._task_scheduler.unschedule(old_current_player_state_id)

        await self._publish_event(
            game=game,
            current_player_id=current_user_id,
        )

        centrifugo_publication = {
            "type": "player_reconnected",
            "player_id": current_user_id.hex,
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
        current_player_id: UserId,
    ) -> None:
        if isinstance(game, ConnectFourGame):
            event = ConnectFourGamePlayerReconnectedEvent(
                game_id=game.id,
                player_id=current_player_id,
            )

        await self._event_publisher.publish(event)
