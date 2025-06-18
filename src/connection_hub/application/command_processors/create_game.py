# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = ("CreateGameCommand", "CreateGameProcessor")

from dataclasses import dataclass

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
        "_transaction_manager",
        "_identity_provider",
    )

    def __init__(
        self,
        create_game: CreateGame,
        lobby_gateway: LobbyGateway,
        game_gateway: GameGateway,
        event_publisher: EventPublisher,
        transaction_manager: TransactionManager,
        identity_provider: IdentityProvider,
    ):
        self._create_game = create_game
        self._lobby_gateway = lobby_gateway
        self._game_gateway = game_gateway
        self._event_publisher = event_publisher
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
