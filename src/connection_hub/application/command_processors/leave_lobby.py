# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from connection_hub.domain.services import LeaveLobby
from connection_hub.application.common import (
    LobbyGateway,
    UserLeftLobbyEvent,
    EventPublisher,
    CentrifugoClient,
    centrifugo_lobby_channel_factory,
    TransactionManager,
    IdentityProvider,
    UserNotInLobbyError,
)


class LeaveLobbyProcessor:
    __slots__ = (
        "_leave_lobby",
        "_lobby_gateway",
        "_event_publisher",
        "_centrifugo_client",
        "_transaction_manager",
        "_identity_provider",
    )

    def __init__(
        self,
        leave_lobby: LeaveLobby,
        lobby_gateway: LobbyGateway,
        event_publisher: EventPublisher,
        centrifugo_client: CentrifugoClient,
        transaction_manager: TransactionManager,
        identity_provider: IdentityProvider,
    ):
        self._leave_lobby = leave_lobby
        self._lobby_gateway = lobby_gateway
        self._event_publisher = event_publisher
        self._centrifugo_client = centrifugo_client
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

        new_admin_id = self._leave_lobby(
            lobby=lobby_to_leave,
            current_user_id=current_user_id,
        )
        await self._lobby_gateway.update(lobby_to_leave)

        event = UserLeftLobbyEvent(
            lobby_id=lobby_to_leave.id,
            user_id=current_user_id,
            new_admin_id=new_admin_id,
        )
        await self._event_publisher.publish(event)

        centrifugo_publication = {
            "type": "user_left",
            "user_id": current_user_id.hex,
            "new_admin_id": new_admin_id.hex if new_admin_id else None,
        }
        await self._centrifugo_client.publish(
            channel=centrifugo_lobby_channel_factory(lobby_to_leave.id),
            data=centrifugo_publication,  # type: ignore[arg-type]
        )

        await self._transaction_manager.commit()
