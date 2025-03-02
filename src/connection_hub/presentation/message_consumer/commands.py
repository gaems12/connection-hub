# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

import logging

from faststream.broker.message import StreamMessage

from connection_hub.application import (
    CreateLobbyCommand,
    JoinLobbyCommand,
    EndGameCommand,
)
from connection_hub.infrastructure import CommonRetort


_logger = logging.getLogger(__name__)


async def _process_stream_message(message: StreamMessage) -> dict:
    decoded_message = await message.decode()

    _logger.debug(
        {
            "message": "Got message from message broker.",
            "decoded_message": message,
        },
    )

    if not decoded_message or not isinstance(decoded_message, dict):
        error_message = "StreamMessage cannot be converted to dict."
        _logger.error(error_message)

        raise Exception(error_message)

    return decoded_message


async def create_lobby_command_factory(
    message: StreamMessage,
    common_retort: CommonRetort,
) -> EndGameCommand:
    decoded_message = await _process_stream_message(message)
    return common_retort.load(decoded_message, CreateLobbyCommand)


async def join_lobby_command_factory(
    message: StreamMessage,
    common_retort: CommonRetort,
) -> EndGameCommand:
    decoded_message = await _process_stream_message(message)
    return common_retort.load(decoded_message, JoinLobbyCommand)


async def end_game_command_factory(
    message: StreamMessage,
    common_retort: CommonRetort,
) -> EndGameCommand:
    decoded_message = await _process_stream_message(message)
    return common_retort.load(decoded_message, EndGameCommand)
