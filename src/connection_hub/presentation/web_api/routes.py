# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from fastapi import APIRouter
from dishka.integrations.fastapi import FromDishka, inject

from connection_hub.application import (
    CreateLobbyCommand,
    CreateLobbyProcessor,
    JoinLobbyCommand,
    JoinLobbyProcessor,
    LeaveLobbyProcessor,
    CreateGameProcessor,
    DisconnectFromGameProcessor,
)


router = APIRouter(prefix="/api/v1/webhooks/centrifugo")


@router.post("/create-lobby")
@inject
async def create_lobby(
    *,
    command: FromDishka[CreateLobbyCommand],
    command_processor: FromDishka[CreateLobbyProcessor],
) -> None:
    await command_processor.process(command)


@router.post("/join-lobby")
@inject
async def join_lobby(
    *,
    command: FromDishka[JoinLobbyCommand],
    command_processor: FromDishka[JoinLobbyProcessor],
) -> None:
    await command_processor.process(command)


@router.delete("/leave-lobby")
@inject
async def leave_lobby(
    *,
    processor: FromDishka[LeaveLobbyProcessor],
) -> None:
    await processor.process()


@router.post("/create-game")
@inject
async def create_game(
    *,
    processor: FromDishka[CreateGameProcessor],
) -> None:
    await processor.process()


@router.delete("/disconnect-from-game")
@inject
async def disconnect_from_game(
    *,
    processor: FromDishka[DisconnectFromGameProcessor],
) -> None:
    await processor.process()
