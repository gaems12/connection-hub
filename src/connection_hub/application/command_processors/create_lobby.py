# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = ("CreateLobbyCommand", "CreateLobbyProcessor")

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Final

from connection_hub.domain import (
    LobbyId,
    UserId,
    ConnectFourRuleSet,
    RuleSet,
    Lobby,
    CreateLobby,
)
from connection_hub.application.common import (
    LobbyGateway,
    GameGateway,
    LobbyCreatedEvent,
    EventPublisher,
    CENTRIFUGO_LOBBY_BROWSER_CHANNEL,
    RemoveFromLobbyTask,
    remove_from_lobby_task_id_factory,
    TaskScheduler,
    CentrifugoPublishCommand,
    CentrifugoClient,
    centrifugo_user_channel_factory,
    TransactionManager,
    IdentityProvider,
    InvalidLobbyNameError,
    InvalidLobbyRuleSetError,
    InvalidLobbyPasswordError,
    CurrentUserInLobbyError,
    CurrentUserInGameError,
)


_MIN_NAME_LENGTH: Final = 3
_MAX_NAME_LENGTH: Final = 128

_MIN_CONNECT_FOUR_TIME_FOR_EACH_PLAYER: Final = timedelta(seconds=30)
_MAX_CONNECT_FOUR_TIME_FOR_EACH_PLAYER: Final = timedelta(minutes=3)

_MIN_PASSWORD_LENGTH: Final = 3
_MAX_PASSWORD_LENGTH: Final = 64


@dataclass(slots=True, kw_only=True)
class CreateLobbyCommand:
    name: str
    rule_set: RuleSet
    password: str | None


class CreateLobbyProcessor:
    __slots__ = (
        "_create_lobby",
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
        create_lobby: CreateLobby,
        lobby_gateway: LobbyGateway,
        game_gateway: GameGateway,
        event_publisher: EventPublisher,
        task_scheduler: TaskScheduler,
        centrifugo_client: CentrifugoClient,
        transaction_manager: TransactionManager,
        identity_provider: IdentityProvider,
    ):
        self._create_lobby = create_lobby
        self._lobby_gateway = lobby_gateway
        self._game_gateway = game_gateway
        self._event_publisher = event_publisher
        self._task_scheduler = task_scheduler
        self._centrifugo_client = centrifugo_client
        self._transaction_manager = transaction_manager
        self._identity_provider = identity_provider

    async def process(self, command: CreateLobbyCommand) -> LobbyId:
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

        self._validate_name(command.name)
        self._validate_rule_set(command.rule_set)

        if command.password:
            self._validate_password(command.password)

        new_lobby = self._create_lobby(
            name=command.name,
            current_user_id=current_user_id,
            rule_set=command.rule_set,
            password=command.password,
        )
        await self._lobby_gateway.save(new_lobby)

        task_id = remove_from_lobby_task_id_factory(
            lobby_id=new_lobby.id,
            user_id=current_user_id,
        )
        execute_task_at = datetime.now(timezone.utc) + timedelta(
            seconds=15,
        )
        task = RemoveFromLobbyTask(
            id=task_id,
            execute_at=execute_task_at,
            lobby_id=new_lobby.id,
            user_id=current_user_id,
        )
        await self._task_scheduler.schedule(task)

        event = LobbyCreatedEvent(
            lobby_id=new_lobby.id,
            name=new_lobby.name,
            admin_id=current_user_id,
            has_password=new_lobby.password is not None,
            rule_set=command.rule_set,
        )
        await self._event_publisher.publish(event)

        await self._publish_data_to_centrifugo(
            lobby=new_lobby,
            rule_set=command.rule_set,
            current_user_id=current_user_id,
        )

        await self._transaction_manager.commit()

        return new_lobby.id

    def _validate_name(self, name: str) -> None:
        if not (_MIN_NAME_LENGTH <= len(name) <= _MAX_NAME_LENGTH):
            raise InvalidLobbyNameError()

    def _validate_rule_set(self, rule_set: RuleSet) -> None:
        if isinstance(rule_set, ConnectFourRuleSet):
            if not (
                _MIN_CONNECT_FOUR_TIME_FOR_EACH_PLAYER
                <= rule_set.time_for_each_player
                <= _MAX_CONNECT_FOUR_TIME_FOR_EACH_PLAYER
            ):
                raise InvalidLobbyRuleSetError()

    def _validate_password(self, password: str) -> None:
        if not (_MIN_PASSWORD_LENGTH <= len(password) <= _MAX_PASSWORD_LENGTH):
            raise InvalidLobbyPasswordError()

    async def _publish_data_to_centrifugo(
        self,
        *,
        lobby: Lobby,
        rule_set: RuleSet,
        current_user_id: UserId,
    ) -> None:
        if isinstance(rule_set, ConnectFourRuleSet):
            rule_set_as_dict = {
                "type": "connect_four",
                "time_for_each_player": (
                    rule_set.time_for_each_player.total_seconds()
                ),
            }

        first_centrifugo_publication = {
            "type": "lobby_created",
            "lobby_id": lobby.id.hex,
            "name": lobby.name,
            "rule_set": rule_set_as_dict,
        }
        first_centrifugo_command = CentrifugoPublishCommand(
            channel=centrifugo_user_channel_factory(current_user_id),
            data=first_centrifugo_publication,  # type: ignore[arg-type]
        )

        second_centrifugo_publication = {
            "type": "lobby_created",
            "lobby_id": lobby.id.hex,
            "name": lobby.name,
            "has_password": lobby.password is not None,
            "rule_set": rule_set_as_dict,
        }
        second_centrifugo_command = CentrifugoPublishCommand(
            channel=CENTRIFUGO_LOBBY_BROWSER_CHANNEL,
            data=second_centrifugo_publication,  # type: ignore[arg-type]
        )

        await self._centrifugo_client.batch(
            commands=[first_centrifugo_command, second_centrifugo_command],
        )
