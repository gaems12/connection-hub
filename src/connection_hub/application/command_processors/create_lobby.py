# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from dataclasses import dataclass
from datetime import timedelta
from typing import Final

from connection_hub.domain import LobbyId, RuleSet, CreateLobby
from connection_hub.application.common import (
    LobbyGateway,
    GameGateway,
    LobbyCreatedEvent,
    EventPublisher,
    TransactionManager,
    IdentityProvider,
    InvalidLobbyNameError,
    InvalidLobbyRuleSetError,
    InvalidLobbyPasswordError,
    UserInLobbyError,
    UserInGameError,
)


_MIN_NAME_LENGTH: Final = 3
_MAX_NAME_LENGTH: Final = 128

_MIN_FOUR_IN_A_ROW_TIME_FOR_EACH_PLAYER: Final = timedelta(seconds=30)
_MAX_FOUR_IN_A_ROW_TIME_FOR_EACH_PLAYER: Final = timedelta(minutes=3)

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
        "_transaction_manager",
        "_identity_provider",
    )

    def __init__(
        self,
        create_lobby: CreateLobby,
        lobby_gateway: LobbyGateway,
        game_gateway: GameGateway,
        event_publisher: EventPublisher,
        transaction_manager: TransactionManager,
        identity_provider: IdentityProvider,
    ):
        self._create_lobby = create_lobby
        self._lobby_gateway = lobby_gateway
        self._game_gateway = game_gateway
        self._event_publisher = event_publisher
        self._transaction_manager = transaction_manager
        self._identity_provider = identity_provider

    async def process(self, command: CreateLobbyCommand) -> LobbyId:
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

        event = LobbyCreatedEvent(
            lobby_id=new_lobby.id,
            name=new_lobby.name,
            admin_id=current_user_id,
            rule_set=command.rule_set,
        )
        await self._event_publisher.publish(event)

        await self._transaction_manager.commit()

        return new_lobby.id

    def _validate_name(self, name: str) -> None:
        if not (_MIN_NAME_LENGTH <= len(name) <= _MAX_NAME_LENGTH):
            raise InvalidLobbyNameError()

    def _validate_rule_set(self, rule_set: RuleSet) -> None:
        if not (
            _MIN_FOUR_IN_A_ROW_TIME_FOR_EACH_PLAYER
            <= rule_set.time_for_each_player
            <= _MAX_FOUR_IN_A_ROW_TIME_FOR_EACH_PLAYER
        ):
            raise InvalidLobbyRuleSetError()

    def _validate_password(self, password: str) -> None:
        if not (_MIN_PASSWORD_LENGTH <= len(password) <= _MAX_PASSWORD_LENGTH):
            raise InvalidLobbyPasswordError()
