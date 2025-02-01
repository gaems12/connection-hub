# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from faststream.nats import NatsMessage

from connection_hub.application import EndGameCommand
from connection_hub.infrastructure import CommonRetort


async def end_game_command_factory(
    message: NatsMessage,
    common_retort: CommonRetort,
) -> EndGameCommand:
    decoded_message = await message.decode()
    if not decoded_message or not isinstance(decoded_message, dict):
        raise Exception("NatsMessage cannot be converted to dict.")

    return common_retort.load(decoded_message, EndGameCommand)
