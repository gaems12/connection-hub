# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = (
    "CENTRIFUGO_LOBBY_BROWSER_CHANNEL",
    "centrifugo_user_channel_factory",
    "centrifugo_lobby_channel_factory",
    "centrifugo_game_channel_factory",
    "Serializable",
    "CentrifugoPublishCommand",
    "CentrifugoUnsubscribeCommand",
    "CentrifugoCommand",
    "CentrifugoClient",
)

from dataclasses import dataclass
from typing import Iterable, Protocol, Final

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


CENTRIFUGO_LOBBY_BROWSER_CHANNEL: Final = "lobby_browser"


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


@dataclass(frozen=True, slots=True, kw_only=True)
class CentrifugoUnsubscribeCommand:
    user: str
    channel: str


type CentrifugoCommand = (
    CentrifugoPublishCommand | CentrifugoUnsubscribeCommand
)


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
