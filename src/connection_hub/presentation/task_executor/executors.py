# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from dishka.integrations.taskiq import FromDishka, inject

from connection_hub.domain import GameId, UserId, PlayerStateId
from connection_hub.application import (
    TryToDisqualifyPlayerCommand,
    TryToDisqualifyPlayerProcessor,
)


@inject
async def try_to_disqualify_player(
    *,
    game_id: GameId,
    player_id: UserId,
    player_state_id: PlayerStateId,
    command_processor: FromDishka[TryToDisqualifyPlayerProcessor],
) -> None:
    command = TryToDisqualifyPlayerCommand(
        game_id=game_id,
        player_id=player_id,
        player_state_id=player_state_id,
    )
    await command_processor.process(command)
