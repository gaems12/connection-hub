# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from dataclasses import dataclass

from lobby.domain import LobbyId, RuleSet, CreateLobby
from lobby.application.common import (
    LobbyGateway,
    GameGateway,
    LobbyCreatedEvent,
    EventPublisher,
    TransactionManager,
    IdentityProvider,
    UserInLobbyError,
    UserInGameError,
)


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

        new_lobby = self._create_lobby(
            name=command.name,
            current_user_id=current_user_id,
            rule_set=command.rule_set,
            password=command.password,
        )
        await self._lobby_gateway.save(new_lobby)

        event = LobbyCreatedEvent(
            id=new_lobby.id,
            name=new_lobby.name,
            admin_id=current_user_id,
            rule_set=command.rule_set,
        )
        await self._event_publisher.publish(event)

        await self._transaction_manager.commit()

        return new_lobby.id
