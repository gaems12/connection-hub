# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from dataclasses import dataclass

from connection_hub.domain import LobbyId, JoinLobby
from connection_hub.application.common import (
    LobbyGateway,
    GameGateway,
    UserJoinedLobbyEvent,
    EventPublisher,
    TransactionManager,
    IdentityProvider,
    UserInLobbyError,
    UserInGameError,
    LobbyDoesNotExistError,
)


@dataclass(frozen=True, slots=True)
class JoinLobbyCommand:
    lobby_id: LobbyId
    password: str | None


class JoinLobbyProcessor:
    __slots__ = (
        "_join_lobby",
        "_lobby_gateway",
        "_game_gateway",
        "_event_publisher",
        "_transaction_manager",
        "_identity_provider",
    )

    def __init__(
        self,
        join_lobby: JoinLobby,
        lobby_gateway: LobbyGateway,
        game_gateway: GameGateway,
        event_publisher: EventPublisher,
        transaction_manager: TransactionManager,
        identity_provider: IdentityProvider,
    ):
        self._join_lobby = join_lobby
        self._lobby_gateway = lobby_gateway
        self._game_gateway = game_gateway
        self._event_publisher = event_publisher
        self._transaction_manager = transaction_manager
        self._identity_provider = identity_provider

    async def process(self, command: JoinLobbyCommand) -> None:
        current_user_id = await self._identity_provider.user_id()

        lobby = await self._lobby_gateway.by_user_id(
            current_user_id,
        )
        if lobby:
            raise UserInLobbyError()

        game = await self._game_gateway.by_player_id(
            current_user_id,
        )
        if game:
            raise UserInGameError()

        lobby_to_join = await self._lobby_gateway.by_id(
            id=command.lobby_id,
            acquire=True,
        )
        if not lobby_to_join:
            raise LobbyDoesNotExistError()

        self._join_lobby(
            lobby=lobby_to_join,
            current_user_id=current_user_id,
            password=command.password,
        )
        await self._lobby_gateway.update(lobby_to_join)

        event = UserJoinedLobbyEvent(
            lobby_id=command.lobby_id,
            user_id=current_user_id,
        )
        await self._event_publisher.publish(event)

        await self._transaction_manager.commit()
