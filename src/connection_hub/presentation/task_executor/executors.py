# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from dishka.integrations.taskiq import FromDishka, inject

from connection_hub.application import (
    TryToDisqualifyPlayerCommand,
    TryToDisqualifyPlayerProcessor,
)


@inject
async def try_to_disqualify_player(
    *,
    command: TryToDisqualifyPlayerCommand,
    command_processor: FromDishka[TryToDisqualifyPlayerProcessor],
) -> None:
    await command_processor.process(command)
