# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from dataclasses import dataclass
from typing import Final

from connection_hub.domain import (
    GameId,
    UserId,
    PlayerStateId,
    TryToDisqualifyPlayer,
    FourInARowGame,
)
from connection_hub.application.common import (
    GameGateway,
    GameType,
    PlayerWasDisqualifiedEvent,
    EventPublisher,
    TransactionManager,
    GameDoesNotExistError,
    UserNotInGameError,
)


_GAME_TO_GAME_TYPE_MAP: Final = {
    FourInARowGame: GameType.FOUR_IN_A_ROW,
}


@dataclass(frozen=True, slots=True)
class DisqualifyPlayerCommand:
    game_id: GameId
    player_id: UserId
    player_state_id: PlayerStateId


class DisqualifyPlayerProcessor:
    __slots__ = (
        "_try_to_disqualify_player",
        "_game_gateway",
        "_event_publisher",
        "_transaction_manager",
    )

    def __init__(
        self,
        try_to_disqualify_player: TryToDisqualifyPlayer,
        game_gateway: GameGateway,
        event_publisher: EventPublisher,
        transaction_manager: TransactionManager,
    ):
        self._try_to_disqualify_player = try_to_disqualify_player
        self._game_gateway = game_gateway
        self._event_publisher = event_publisher
        self._transaction_manager = transaction_manager

    async def process(self, command: DisqualifyPlayerCommand) -> None:
        game = await self._game_gateway.by_id(
            game_id=command.game_id,
            acquire=True,
        )
        if not game:
            raise GameDoesNotExistError()

        if command.player_id not in game.players:
            raise UserNotInGameError()

        player_is_disqualified, game_is_ended = self._try_to_disqualify_player(
            game=game,
            player_id=command.player_id,
            player_state_id=command.player_state_id,
        )
        if not player_is_disqualified:
            return

        if game_is_ended:
            await self._game_gateway.delete(game)
        else:
            await self._game_gateway.update(game)

        event = PlayerWasDisqualifiedEvent(
            game_id=command.game_id,
            game_type=_GAME_TO_GAME_TYPE_MAP[type(game)],
            player_id=command.player_id,
        )
        await self._event_publisher.publish(event)

        await self._transaction_manager.commit()
