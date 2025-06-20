# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = (
    "create_lobby",
    "join_lobby",
    "leave_lobby",
    "kick_from_lobby",
    "create_game",
    "start_game",
    "end_game",
    "acknowledge_presence",
    "reconnect_to_game",
)

from typing import Final

from faststream.nats import NatsRouter, JStream, PullSub
from dishka.integrations.faststream import FromDishka, inject

from connection_hub.application import (
    CreateLobbyCommand,
    CreateLobbyProcessor,
    JoinLobbyCommand,
    JoinLobbyProcessor,
    LeaveLobbyCommand,
    LeaveLobbyProcessor,
    KickFromLobbyCommand,
    KickFromLobbyProcessor,
    CreateGameCommand,
    CreateGameProcessor,
    StartGameCommand,
    StartGameProcessor,
    EndGameCommand,
    EndGameProcessor,
    AcknowledgePresenceProcessor,
    ReconnectToGameCommand,
    ReconnectToGameProcessor,
)


_STREAM: Final = JStream(name="games", declare=False)

router: Final = NatsRouter()


@router.subscriber(
    subject="gaems12.api_gateway.lobby.created",
    durable="connection_hub_lobby_created",
    stream=_STREAM,
    pull_sub=PullSub(timeout=0.2),
)
@inject
async def create_lobby(
    *,
    command: CreateLobbyCommand,
    command_processor: FromDishka[CreateLobbyProcessor],
) -> None:
    await command_processor.process(command)


@router.subscriber(
    subject="gaems12.api_gateway.lobby.user_joined",
    durable="connection_hub_lobby_user_joined",
    stream=_STREAM,
    pull_sub=PullSub(timeout=0.2),
)
@inject
async def join_lobby(
    *,
    command: JoinLobbyCommand,
    command_processor: FromDishka[JoinLobbyProcessor],
) -> None:
    await command_processor.process(command)


@router.subscriber(
    subject="gaems12.api_gateway.lobby.user_left",
    durable="connection_hub_lobby_user_left",
    stream=_STREAM,
    pull_sub=PullSub(timeout=0.2),
)
@inject
async def leave_lobby(
    *,
    command: LeaveLobbyCommand,
    command_processor: FromDishka[LeaveLobbyProcessor],
) -> None:
    await command_processor.process(command)


@router.subscriber(
    subject="gaems12.api_gateway.lobby.user_kicked",
    durable="connection_hub_lobby_user_kicked",
    stream=_STREAM,
    pull_sub=PullSub(timeout=0.2),
)
@inject
async def kick_from_lobby(
    *,
    command: KickFromLobbyCommand,
    command_processor: FromDishka[KickFromLobbyProcessor],
) -> None:
    await command_processor.process(command)


@router.subscriber(
    subject="gaems12.api_gateway.game.created",
    durable="connection_hub_game_created",
    stream=_STREAM,
    pull_sub=PullSub(timeout=0.2),
)
@inject
async def create_game(
    *,
    command: CreateGameCommand,
    command_processor: FromDishka[CreateGameProcessor],
) -> None:
    await command_processor.process(command)


@router.subscriber(
    subject="gaems12.connect_four.game.created",
    durable="connection_hub_game_started",
    stream=_STREAM,
    pull_sub=PullSub(timeout=0.2),
)
@inject
async def start_game(
    *,
    command: StartGameCommand,
    command_processor: FromDishka[StartGameProcessor],
) -> None:
    await command_processor.process(command)


@router.subscriber(
    subject="gaems12.*.game.ended",
    durable="connection_hub_game_ended",
    stream=_STREAM,
    pull_sub=PullSub(timeout=0.2),
)
@inject
async def end_game(
    *,
    command: EndGameCommand,
    command_processor: FromDishka[EndGameProcessor],
) -> None:
    await command_processor.process(command)


@router.subscriber(
    subject="gaems12.api_gateway.presence.acknowledged",
    durable="connection_hub_presence_acknowledged",
    stream=_STREAM,
    pull_sub=PullSub(timeout=0.2),
)
@inject
async def acknowledge_presence(
    *,
    processor: FromDishka[AcknowledgePresenceProcessor],
) -> None:
    await processor.process()


@router.subscriber(
    subject="gaems12.api_gateway.game.player_reconnected",
    durable="connection_hub_game_player_reconnected",
    stream=_STREAM,
    pull_sub=PullSub(timeout=0.2),
)
@inject
async def reconnect_to_game(
    *,
    command: ReconnectToGameCommand,
    command_processor: FromDishka[ReconnectToGameProcessor],
) -> None:
    await command_processor.process(command)
