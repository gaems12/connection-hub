# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = ("JoinLobbyCommand", "JoinLobbyProcessor")

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from connection_hub.domain import LobbyId, UserId, Lobby, JoinLobby
from connection_hub.application.common import (
    LobbyGateway,
    GameGateway,
    UserJoinedLobbyEvent,
    EventPublisher,
    RemoveFromLobbyTask,
    remove_from_lobby_task_id_factory,
    TaskScheduler,
    Serializable,
    CentrifugoPublishCommand,
    CentrifugoClient,
    centrifugo_user_channel_factory,
    centrifugo_lobby_channel_factory,
    TransactionManager,
    IdentityProvider,
    CurrentUserInLobbyError,
    CurrentUserInGameError,
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
        "_task_scheduler",
        "_centrifugo_client",
        "_transaction_manager",
        "_identity_provider",
    )

    def __init__(
        self,
        join_lobby: JoinLobby,
        lobby_gateway: LobbyGateway,
        game_gateway: GameGateway,
        event_publisher: EventPublisher,
        task_scheduler: TaskScheduler,
        centrifugo_client: CentrifugoClient,
        transaction_manager: TransactionManager,
        identity_provider: IdentityProvider,
    ):
        self._join_lobby = join_lobby
        self._lobby_gateway = lobby_gateway
        self._game_gateway = game_gateway
        self._event_publisher = event_publisher
        self._task_scheduler = task_scheduler
        self._centrifugo_client = centrifugo_client
        self._transaction_manager = transaction_manager
        self._identity_provider = identity_provider

    async def process(self, command: JoinLobbyCommand) -> None:
        current_user_id = await self._identity_provider.user_id()

        lobby = await self._lobby_gateway.by_user_id(
            current_user_id,
        )
        if lobby:
            raise CurrentUserInLobbyError()

        game = await self._game_gateway.by_player_id(
            current_user_id,
        )
        if game:
            raise CurrentUserInGameError()

        lobby_to_join = await self._lobby_gateway.by_id(
            lobby_id=command.lobby_id,
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

        task_id = remove_from_lobby_task_id_factory(
            lobby_id=lobby_to_join.id,
            user_id=current_user_id,
        )
        execute_task_at = datetime.now(timezone.utc) + timedelta(
            seconds=15,
        )
        task = RemoveFromLobbyTask(
            id=task_id,
            execute_at=execute_task_at,
            lobby_id=lobby_to_join.id,
            user_id=current_user_id,
        )
        await self._task_scheduler.schedule(task)

        event = UserJoinedLobbyEvent(
            lobby_id=command.lobby_id,
            user_id=current_user_id,
        )
        await self._event_publisher.publish(event)

        await self._make_requests_to_centrifugo(
            lobby=lobby_to_join,
            current_user_id=current_user_id,
        )

        await self._transaction_manager.commit()

    async def _make_requests_to_centrifugo(
        self,
        *,
        lobby: Lobby,
        current_user_id: UserId,
    ) -> None:
        first_centrifugo_publication: Serializable = {
            "type": "user_joined",
            "user_id": current_user_id.hex,
        }
        first_centrifugo_command = CentrifugoPublishCommand(
            channel=centrifugo_lobby_channel_factory(lobby.id),
            data=first_centrifugo_publication,
        )

        raw_users: Serializable = {
            user_id.hex: user_role
            for user_id, user_role in lobby.users.items()
        }
        second_centrifugo_publication: Serializable = {
            "type": "joined_to_lobby",
            "users": raw_users,
        }
        second_centrifugo_command = CentrifugoPublishCommand(
            channel=centrifugo_user_channel_factory(current_user_id),
            data=second_centrifugo_publication,
        )

        await self._centrifugo_client.batch(
            commands=[first_centrifugo_command, second_centrifugo_command],
        )
