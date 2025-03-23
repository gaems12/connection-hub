# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from dishka.integrations.taskiq import FromDishka, inject

from connection_hub.domain import DomainError
from connection_hub.application import (
    ApplicationError,
    RemoveFromLobbyCommand,
    RemoveFromLobbyProcessor,
    DisconnectFromGameCommand,
    DisconnectFromGameProcessor,
    TryToDisqualifyPlayerCommand,
    TryToDisqualifyPlayerProcessor,
)


@inject
async def remove_from_lobby(
    *,
    command: RemoveFromLobbyCommand,
    command_processor: RemoveFromLobbyProcessor,
) -> None:
    try:
        await command_processor.process(command)
    except (DomainError, ApplicationError):
        return


@inject
async def disconnect_from_game(
    *,
    command: DisconnectFromGameCommand,
    command_processor: FromDishka[DisconnectFromGameProcessor],
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
