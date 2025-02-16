# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from typing import Final

from faststream.nats import NatsRouter, JStream, PullSub
from dishka.integrations.faststream import FromDishka, inject

from connection_hub.application import (
    CreateLobbyCommand,
    CreateLobbyProcessor,
    JoinLobbyCommand,
    JoinLobbyProcessor,
    LeaveLobbyProcessor,
    CreateGameProcessor,
    EndGameCommand,
    EndGameProcessor,
    DisconnectFromGameProcessor,
    ReconnectToGameProcessor,
)


_API_GATEWAY_STREAM: Final = JStream("api_gateway")
_FOUR_IN_A_ROW_STREAM: Final = JStream("four_in_a_row")


router = NatsRouter()


@router.subscriber(
    subject="lobby.created",
    durable="connection_hub.lobby.created",
    stream=_API_GATEWAY_STREAM,
    pull_sub=PullSub(timeout=0.2),
)
@inject
async def create_lobby(
    *,
    command: FromDishka[CreateLobbyCommand],
    command_processor: FromDishka[CreateLobbyProcessor],
) -> None:
    await command_processor.process(command)


@router.subscriber(
    subject="lobby.user_joined",
    durable="connection_hub.lobby.user_joined",
    stream=_API_GATEWAY_STREAM,
    pull_sub=PullSub(timeout=0.2),
)
@inject
async def join_lobby(
    *,
    command: FromDishka[JoinLobbyCommand],
    command_processor: FromDishka[JoinLobbyProcessor],
) -> None:
    await command_processor.process(command)


@router.subscriber(
    subject="lobby.user_left",
    durable="connection_hub.lobby.user_left",
    stream=_API_GATEWAY_STREAM,
    pull_sub=PullSub(timeout=0.2),
)
@inject
async def leave_lobby(
    *,
    processor: FromDishka[LeaveLobbyProcessor],
) -> None:
    await processor.process()


@router.subscriber(
    subject="game.created",
    durable="connection_hub.game.created",
    stream=_API_GATEWAY_STREAM,
    pull_sub=PullSub(timeout=0.2),
)
@inject
async def create_game(
    *,
    processor: FromDishka[CreateGameProcessor],
) -> None:
    await processor.process()


@router.subscriber(
    subject="game.ended",
    durable="connection_hub.game_ended",
    stream=_FOUR_IN_A_ROW_STREAM,
    pull_sub=PullSub(timeout=0.2),
)
@inject
async def end_game(
    *,
    command: FromDishka[EndGameCommand],
    command_processor: FromDishka[EndGameProcessor],
) -> None:
    await command_processor.process(command)


@router.subscriber(
    subject="game.player_disconnected",
    durable="connection_hub.game.player_disconnected",
    stream=_API_GATEWAY_STREAM,
    pull_sub=PullSub(timeout=0.2),
)
@inject
async def disconnect_from_game(
    *,
    processor: FromDishka[DisconnectFromGameProcessor],
) -> None:
    await processor.process()


@router.subscriber(
    subject="game.player_reconnected",
    durable="connection_hub.game.player_reconnected",
    stream=_API_GATEWAY_STREAM,
    pull_sub=PullSub(timeout=0.2),
)
@inject
async def reconnect_to_game(
    *,
    processor: FromDishka[ReconnectToGameProcessor],
) -> None:
    await processor.process()
