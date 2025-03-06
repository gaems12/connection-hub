# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from datetime import datetime, timezone

from connection_hub.domain import (
    UserId,
    ConnectFourGame,
    Game,
    DisconnectFromGame,
)
from connection_hub.application.common import (
    GameGateway,
    ConnectFourGamePlayerDisconnectedEvent,
    EventPublisher,
    TryToDisqualifyPlayerTask,
    TaskScheduler,
    CentrifugoClient,
    centrifugo_game_channel_factory,
    TransactionManager,
    IdentityProvider,
    UserNotInGameError,
)


class DisconnectFromGameProcessor:
    __slots__ = (
        "_disconnect_from_game",
        "_game_gateway",
        "_task_scheduler",
        "_event_publisher",
        "_centrifugo_client",
        "_transaction_manager",
        "_identity_provider",
    )

    def __init__(
        self,
        disconnect_from_game: DisconnectFromGame,
        game_gateway: GameGateway,
        task_scheduler: TaskScheduler,
        event_publisher: EventPublisher,
        centrifugo_client: CentrifugoClient,
        transaction_manager: TransactionManager,
        identity_provider: IdentityProvider,
    ):
        self._disconnect_from_game = disconnect_from_game
        self._game_gateway = game_gateway
        self._task_scheduler = task_scheduler
        self._event_publisher = event_publisher
        self._centrifugo_client = centrifugo_client
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

        self._disconnect_from_game(
            game=game,
            current_user_id=current_user_id,
        )
        await self._game_gateway.update(game)

        current_player_state = game.players[current_user_id]
        time_left_for_current_player = current_player_state.time_left

        execute_task_at = (
            datetime.now(timezone.utc) + time_left_for_current_player
        )
        task = TryToDisqualifyPlayerTask(
            id=current_player_state.id,
            execute_at=execute_task_at,
            game_id=game.id,
            player_id=current_user_id,
            player_state_id=current_player_state.id,
        )
        await self._task_scheduler.schedule(task)

        await self._publish_event(
            game=game,
            current_player_id=current_user_id,
        )

        centrfugo_publication = {
            "type": "player_disconnected",
            "player_id": current_user_id.hex,
        }
        await self._centrifugo_client.publish(
            channel=centrifugo_game_channel_factory(game.id),
            data=centrfugo_publication,  # type: ignore[arg-type]
        )

        await self._transaction_manager.commit()

    async def _publish_event(
        self,
        *,
        game: Game,
        current_player_id: UserId,
    ) -> None:
        if isinstance(game, ConnectFourGame):
            event = ConnectFourGamePlayerDisconnectedEvent(
                game_id=game.id,
                player_id=current_player_id,
            )

        await self._event_publisher.publish(event)
