# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from fastapi import Request

from connection_hub.application import CreateLobbyCommand, JoinLobbyCommand
from connection_hub.infrastructure import CommonRetort


async def create_lobby_command_factory(
    request: Request,
    common_retort: CommonRetort,
) -> CreateLobbyCommand:
    request_json = await request.json()
    if not request_json or not isinstance(request_json, dict):
        raise Exception("HTTP request's JSON cannot be converted to dict.")

    return common_retort.load(request_json, CreateLobbyCommand)


async def join_lobby_command_factory(
    request: Request,
    common_retort: CommonRetort,
) -> JoinLobbyCommand:
    request_json = await request.json()
    if not request_json or not isinstance(request_json, dict):
        raise Exception("HTTP request's JSON cannot be converted to dict.")

    return common_retort.load(request_json, JoinLobbyCommand)
