# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from connection_hub.domain import (
    LobbyId,
    FourInARowGame,
    Game,
    CreateGame,
)
from connection_hub.application.common import (
    LobbyGateway,
    GameGateway,
    FourInARowGameCreatedEvent,
    EventPublisher,
    TransactionManager,
    IdentityProvider,
    UserNotInLobbyError,
)


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

    async def process(self) -> None:
        current_user_id = await self._identity_provider.user_id()

        lobby = await self._lobby_gateway.by_user_id(
            user_id=current_user_id,
            acquire=True,
        )
        if not lobby:
            raise UserNotInLobbyError()

        new_game = self._create_game(
            lobby=lobby,
            current_user_id=current_user_id,
        )
        await self._game_gateway.save(new_game)

        await self._publish_game(lobby_id=lobby.id, game=new_game)

        await self._transaction_manager.commit()

    async def _publish_game(
        self,
        *,
        lobby_id: LobbyId,
        game: Game,
    ) -> None:
        if isinstance(game, FourInARowGame):
            event = FourInARowGameCreatedEvent(
                game_id=game.id,
                lobby_id=lobby_id,
                first_player_id=game.players[0],
                second_player_id=game.players[1],
                time_for_each_player=game.time_for_each_player,
                created_at=game.created_at,
            )
            await self._event_publisher.publish(event)
