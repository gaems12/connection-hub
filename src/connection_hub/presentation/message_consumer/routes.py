# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from faststream.nats import NatsRouter
from dishka.integrations.faststream import FromDishka, inject

from connection_hub.application import EndGameCommand, EndGameProcessor


router = NatsRouter()


@router.subscriber(
    subject="game.ended",
    queue="connection_hub.game_ended",
    durable="connection_hub.game_ended",
    stream="four_in_a_row",
)
@inject
async def end_game(
    *,
    command: EndGameCommand,
    command_processor: FromDishka[EndGameProcessor],
) -> None:
    await command_processor.process(command)
