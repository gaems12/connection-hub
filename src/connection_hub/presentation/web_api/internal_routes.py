# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from fastapi import APIRouter
from dishka.integrations.fastapi import FromDishka, inject

from connection_hub.application import (
    LeaveLobbyProcessor,
    CreateGameProcessor,
    DisconnectFromGameProcessor,
)


internal_router = APIRouter(
    prefix="/internal/api/v1/webhooks/centrifugo",
    tags=["internal", "centrifugo"],
)


@internal_router.delete("/leave-lobby")
@inject
async def leave_lobby(
    *,
    processor: FromDishka[LeaveLobbyProcessor],
) -> None:
    await processor.process()


@internal_router.post("/create-game")
@inject
async def create_game(
    *,
    processor: FromDishka[CreateGameProcessor],
) -> None:
    await processor.process()


@internal_router.delete("/disconnect-from-game")
@inject
async def disconnect_from_game(
    *,
    processor: FromDishka[DisconnectFromGameProcessor],
) -> None:
    await processor.process()
