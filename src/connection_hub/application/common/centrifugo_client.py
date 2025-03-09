# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = (
    "centrifugo_user_channel_factory",
    "centrifugo_lobby_channel_factory",
    "centrifugo_game_channel_factory",
    "Serializable",
    "CentrifugoPublishCommand",
    "CentrifugoCommand",
    "CentrifugoClient",
)

from dataclasses import dataclass
from typing import Iterable, Protocol

from connection_hub.domain import GameId, UserId, LobbyId


type Serializable = (
    str
    | int
    | float
    | bytes
    | None
    | list[Serializable]
    | dict[str, Serializable]
)


def centrifugo_user_channel_factory(user_id: UserId) -> str:
    return f"#{user_id.hex}"


def centrifugo_lobby_channel_factory(lobby_id: LobbyId) -> str:
    return f"lobbies:{lobby_id.hex}"


def centrifugo_game_channel_factory(game_id: GameId) -> str:
    return f"games:{game_id.hex}"


@dataclass(frozen=True, slots=True, kw_only=True)
class CentrifugoPublishCommand:
    channel: str
    data: Serializable


type CentrifugoCommand = CentrifugoPublishCommand


class CentrifugoClient(Protocol):
    async def publish(
        self,
        *,
        channel: str,
        data: Serializable,
    ) -> None:
        raise NotImplementedError

    async def batch(
        self,
        *,
        commands: Iterable[CentrifugoCommand],
        parallel: bool = True,
    ) -> None:
        raise NotImplementedError
