# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = ("LeaveLobbyCommand", "LeaveLobbyProcessor")

from dataclasses import dataclass

from connection_hub.domain import (
    LobbyId,
    UserId,
    Lobby,
    RemoveFromLobby,
)
from connection_hub.application.common import (
    LobbyGateway,
    UserLeftLobbyEvent,
    EventPublisher,
    remove_from_lobby_task_id_factory,
    TaskScheduler,
    CentrifugoPublishCommand,
    CentrifugoUnsubscribeCommand,
    CentrifugoCommand,
    CentrifugoClient,
    centrifugo_lobby_channel_factory,
    TransactionManager,
    IdentityProvider,
    LobbyDoesNotExistError,
    CurrentUserNotInLobbyError,
)


@dataclass(frozen=True, slots=True)
class LeaveLobbyCommand:
    lobby_id: LobbyId


class LeaveLobbyProcessor:
    __slots__ = (
        "_remove_from_lobby",
        "_lobby_gateway",
        "_event_publisher",
        "_task_scheduler",
        "_centrifugo_client",
        "_transaction_manager",
        "_identity_provider",
    )

    def __init__(
        self,
        remove_from_lobby: RemoveFromLobby,
        lobby_gateway: LobbyGateway,
        event_publisher: EventPublisher,
        task_scheduler: TaskScheduler,
        centrifugo_client: CentrifugoClient,
        transaction_manager: TransactionManager,
        identity_provider: IdentityProvider,
    ):
        self._remove_from_lobby = remove_from_lobby
        self._lobby_gateway = lobby_gateway
        self._event_publisher = event_publisher
        self._task_scheduler = task_scheduler
        self._centrifugo_client = centrifugo_client
        self._transaction_manager = transaction_manager
        self._identity_provider = identity_provider

    async def process(self, command: LeaveLobbyCommand) -> None:
        current_user_id = await self._identity_provider.user_id()

        lobby = await self._lobby_gateway.by_id(
            lobby_id=command.lobby_id,
            acquire=True,
        )
        if not lobby:
            raise LobbyDoesNotExistError()

        if current_user_id not in lobby.users:
            raise CurrentUserNotInLobbyError()

        no_users_left, new_admin_id = self._remove_from_lobby(
            lobby=lobby,
            user_id=current_user_id,
        )
        if no_users_left:
            await self._lobby_gateway.delete(lobby)
        else:
            await self._lobby_gateway.update(lobby)

        task_id = remove_from_lobby_task_id_factory(
            lobby_id=lobby.id,
            user_id=current_user_id,
        )
        await self._task_scheduler.unschedule(task_id)

        event = UserLeftLobbyEvent(
            lobby_id=lobby.id,
            user_id=current_user_id,
            new_admin_id=new_admin_id,
        )
        await self._event_publisher.publish(event)

        await self._make_requests_to_centrifugo(
            lobby=lobby,
            lobby_is_deleted=no_users_left,
            new_admin_id=new_admin_id,
            current_user_id=current_user_id,
        )

        await self._transaction_manager.commit()

    async def _make_requests_to_centrifugo(
        self,
        *,
        lobby: Lobby,
        lobby_is_deleted: bool,
        new_admin_id: UserId | None,
        current_user_id: UserId,
    ) -> None:
        lobby_channel = centrifugo_lobby_channel_factory(lobby.id)

        centrifugo_commands: list[CentrifugoCommand] = [
            CentrifugoUnsubscribeCommand(
                user=current_user_id.hex,
                channel=lobby_channel,
            ),
        ]
        if not lobby_is_deleted:
            centrifugo_publication = {
                "type": "user_left",
                "user_id": current_user_id.hex,
                "new_admin_id": new_admin_id.hex if new_admin_id else None,
            }
            centrifugo_command = CentrifugoPublishCommand(
                channel=lobby_channel,
                data=centrifugo_publication,  # type: ignore[arg-type]
            )
            centrifugo_commands.append(centrifugo_command)

        await self._centrifugo_client.batch(commands=centrifugo_commands)
