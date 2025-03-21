# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from dishka.integrations.taskiq import FromDishka, inject

from connection_hub.domain import DomainError
from connection_hub.application import (
    ApplicationError,
    ForceLeaveLobbyCommand,
    ForceLeaveLobbyProcessor,
    TryToDisqualifyPlayerCommand,
    TryToDisqualifyPlayerProcessor,
)


@inject
async def force_leave_lobby(
    *,
    command: ForceLeaveLobbyCommand,
    command_processor: ForceLeaveLobbyProcessor,
) -> None:
    try:
        await command_processor.process(command)
    except (DomainError, ApplicationError):
        return


@inject
async def try_to_disqualify_player(
    *,
    command: TryToDisqualifyPlayerCommand,
    command_processor: FromDishka[TryToDisqualifyPlayerProcessor],
) -> None:
    try:
        await command_processor.process(command)
    except (DomainError, ApplicationError):
        return
