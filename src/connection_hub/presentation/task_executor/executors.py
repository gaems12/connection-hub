# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from dishka.integrations.taskiq import FromDishka, inject

from connection_hub.domain import GameId, UserId, PlayerStateId
from connection_hub.application import (
    TryToDisqualifyPlayerCommand,
    TryToDisqualifyPlayerProcessor,
)
from .context_var_setter import ContextVarSetter


@inject
async def try_to_disqualify_player(
    *,
    game_id: GameId,
    player_id: UserId,
    player_state_id: PlayerStateId,
    context_var_setter: FromDishka[ContextVarSetter],
    command_processor: FromDishka[TryToDisqualifyPlayerProcessor],
) -> None:
    context_var_setter.set()

    command = TryToDisqualifyPlayerCommand(
        game_id=game_id,
        player_id=player_id,
        player_state_id=player_state_id,
    )
    await command_processor.process(command)
