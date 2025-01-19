# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from fastapi import Request

from lobby.application import CreateLobbyCommand
from lobby.infrastructure import CommonRetort


async def create_lobby_command_factory(
    request: Request,
    common_retort: CommonRetort,
) -> CreateLobbyCommand:
    request_json = await request.json()
    if not request_json or not isinstance(request_json, dict):
        raise Exception("HTTP request's JSON cannot be converter to dict.")

    return common_retort.load(request_json, CreateLobbyCommand)
