# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from dataclasses import dataclass

from connection_hub.domain import (
    LobbyId,
    UserId,
    LeaveLobby,
    Lobby,
)
from connection_hub.application.common import (
    LobbyGateway,
    UserLeftLobbyEvent,
    EventPublisher,
    CentrifugoUnsubscribeCommand,
    CentrifugoPublishCommand,
    CentrifugoCommand,
    CentrifugoClient,
    centrifugo_lobby_channel_factory,
    TransactionManager,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ForceLeaveLobbyCommand:
    lobby_id: LobbyId
    user_id: UserId


class ForceLeaveLobbyProcessor:
    __slots__ = (
        "_leave_lobby",
        "_lobby_gateway",
        "_event_publisher",
        "_centrifugo_client",
        "_transaction_manager",
    )

    def __init__(
        self,
        leave_lobby: LeaveLobby,
        lobby_gateway: LobbyGateway,
        event_publisher: EventPublisher,
        centrifugo_client: CentrifugoClient,
        transaction_manager: TransactionManager,
    ):
        self._leave_lobby = leave_lobby
        self._lobby_gateway = lobby_gateway
        self._event_publisher = event_publisher
        self._centrifugo_client = centrifugo_client
        self._transaction_manager = transaction_manager

    async def process(self, command: ForceLeaveLobbyCommand) -> None:
        lobby = await self._lobby_gateway.by_id(
            id=command.lobby_id,
            acquire=True,
        )
        if not lobby or command.user_id not in lobby.users:
            return

        no_users_left, new_admin_id = self._leave_lobby(
            lobby=lobby,
            user_id=command.user_id,
        )
        if no_users_left:
            await self._lobby_gateway.delete(lobby)
        else:
            await self._lobby_gateway.update(lobby)

        event = UserLeftLobbyEvent(
            lobby_id=lobby.id,
            user_id=command.user_id,
            new_admin_id=new_admin_id,
        )
        await self._event_publisher.publish(event)

        await self._publish_data_to_centrifugo(
            lobby=lobby,
            lobby_is_deleted=no_users_left,
            new_admin_id=new_admin_id,
            user_id=command.user_id,
        )

        await self._transaction_manager.commit()

    async def _publish_data_to_centrifugo(
        self,
        *,
        lobby: Lobby,
        lobby_is_deleted: bool,
        new_admin_id: UserId | None,
        user_id: UserId,
    ) -> None:
        lobby_channel = centrifugo_lobby_channel_factory(lobby.id)

        centrifugo_commands: list[CentrifugoCommand] = [
            CentrifugoUnsubscribeCommand(
                user=user_id.hex,
                channel=lobby_channel,
            ),
        ]
        if not lobby_is_deleted:
            centrifugo_publication = {
                "type": "user_left",
                "user_id": user_id.hex,
                "new_admin_id": new_admin_id.hex if new_admin_id else None,
            }
            centrifugo_command = CentrifugoPublishCommand(
                channel=lobby_channel,
                data=centrifugo_publication,  # type: ignore[arg-type]
            )
            centrifugo_commands.append(centrifugo_command)

        await self._centrifugo_client.batch(commands=centrifugo_commands)
