# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from connection_hub.domain.services import LeaveLobby
from connection_hub.application.common import (
    LobbyGateway,
    UserLeftLobbyEvent,
    EventPublisher,
    TransactionManager,
    IdentityProvider,
    UserNotInLobbyError,
)


class LeaveLobbyProcessor:
    __slots__ = (
        "_leave_lobby",
        "_lobby_gateway",
        "_event_publisher",
        "_transaction_manager",
        "_identity_provider",
    )

    def __init__(
        self,
        leave_lobby: LeaveLobby,
        lobby_gateway: LobbyGateway,
        event_publisher: EventPublisher,
        transaction_manager: TransactionManager,
        identity_provider: IdentityProvider,
    ):
        self._leave_lobby = leave_lobby
        self._lobby_gateway = lobby_gateway
        self._event_publisher = event_publisher
        self._transaction_manager = transaction_manager
        self._identity_provider = identity_provider

    async def process(self) -> None:
        current_user_id = await self._identity_provider.user_id()

        lobby_to_leave = await self._lobby_gateway.by_user_id(
            user_id=current_user_id,
            acquire=True,
        )
        if not lobby_to_leave:
            raise UserNotInLobbyError()

        self._leave_lobby(
            lobby=lobby_to_leave,
            current_user_id=current_user_id,
        )
        await self._lobby_gateway.update(lobby_to_leave)

        event = UserLeftLobbyEvent(
            lobby_id=lobby_to_leave.id,
            user_id=current_user_id,
        )
        await self._event_publisher.publish(event)

        await self._transaction_manager.commit()
