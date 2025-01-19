# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from fastapi import APIRouter
from dishka.integrations.fastapi import FromDishka, inject

from lobby.domain import LobbyId
from lobby.application import CreateLobbyCommand, CreateLobbyProcessor


internal_router = APIRouter(
    prefix="/api/v1/internal",
    tags=["internal"],
)


@internal_router.post("/lobbies")
@inject
async def create_lobby(
    *,
    command: FromDishka[CreateLobbyCommand],
    command_processor: FromDishka[CreateLobbyProcessor],
) -> LobbyId:
    return await command_processor.process(command)
