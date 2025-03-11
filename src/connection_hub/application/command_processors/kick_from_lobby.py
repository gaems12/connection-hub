# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from dataclasses import dataclass

from connection_hub.domain import LobbyId, UserId, KickFromLobby
from connection_hub.application.common import (
    LobbyGateway,
    UserKickedFromLobbyEvent,
    EventPublisher,
    CentrifugoPublishCommand,
    CentrifugoUnsubscribeCommand,
    centrifugo_lobby_channel_factory,
    CentrifugoClient,
    TransactionManager,
    IdentityProvider,
    LobbyDoesNotExistError,
    UserNotInLobbyError,
)


@dataclass(frozen=True, slots=True)
class KickFromLobbyCommand:
    user_id: UserId


class KickFromLobbyProcessor:
    __slots__ = (
        "_kick_from_lobby",
        "_lobby_gateway",
        "_event_publisher",
        "_centrifugo_client",
        "_transation_manager",
        "_identity_provider",
    )

    def __init__(
        self,
        kick_from_lobby: KickFromLobby,
        lobby_gateway: LobbyGateway,
        event_publisher: EventPublisher,
        centrifugo_client: CentrifugoClient,
        tranaction_manager: TransactionManager,
        identity_provider: IdentityProvider,
    ):
        self._kick_from_lobby = kick_from_lobby
        self._lobby_gateway = lobby_gateway
        self._event_publisher = event_publisher
        self._centrifugo_client = centrifugo_client
        self._transation_manager = tranaction_manager
        self._identity_provider = identity_provider

    async def process(self, command: KickFromLobbyCommand) -> None:
        current_user_id = await self._identity_provider.user_id()

        lobby = await self._lobby_gateway.by_user_id(
            user_id=current_user_id,
            acquire=True,
        )
        if not lobby:
            raise LobbyDoesNotExistError()

        if command.user_id not in lobby.users:
            raise UserNotInLobbyError()

        self._kick_from_lobby(
            lobby=lobby,
            user_to_kick=command.user_id,
            current_user_id=current_user_id,
        )
        await self._lobby_gateway.update(lobby)

        event = UserKickedFromLobbyEvent(
            lobby_id=lobby.id,
            user_id=command.user_id,
        )
        await self._event_publisher.publish(event)

        await self._publish_data_to_centrifugo(
            lobby_id=lobby.id,
            user_id=command.user_id,
        )

        await self._transation_manager.commit()

    async def _publish_data_to_centrifugo(
        self,
        *,
        lobby_id: LobbyId,
        user_id: UserId,
    ) -> None:
        channel = centrifugo_lobby_channel_factory(lobby_id)

        centrifugo_publication = {
            "type": "user_kicked",
            "lobby_id": lobby_id.hex,
            "user_id": user_id.hex,
        }
        first_centrifugo_command = CentrifugoPublishCommand(
            channel=channel,
            data=centrifugo_publication,  # type: ignore[arg-type]
        )
        second_centrifugo_command = CentrifugoUnsubscribeCommand(
            user=user_id.hex,
            channel=channel,
        )

        await self._centrifugo_client.batch(
            commands=[first_centrifugo_command, second_centrifugo_command],
        )
