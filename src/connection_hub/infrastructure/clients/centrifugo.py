# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from urllib.parse import urljoin
from dataclasses import dataclass

from httpx import AsyncClient

from connection_hub.domain import LobbyId
from connection_hub.application import (
    UserJoinedLobbyEvent,
    UserLeftLobbyEvent,
    Event,
)
from connection_hub.infrastructure.utils import get_env_var


type _Serializable = (
    str
    | int
    | float
    | bytes
    | None
    | list[_Serializable]
    | dict[str, _Serializable]
)


def load_centrifugo_config() -> "CentrifugoConfig":
    return CentrifugoConfig(
        url=get_env_var("CENTRIFUGO_URL"),
        api_key=get_env_var("CENTRIFUGO_API_KEY"),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class CentrifugoConfig:
    url: str
    api_key: str


class HTTPXCentrifugoClient:
    __slots__ = ("_httpx_client", "_config")

    def __init__(
        self,
        httpx_client: AsyncClient,
        config: CentrifugoConfig,
    ):
        self._httpx_client = httpx_client
        self._config = config

    async def publish_event(self, event: Event) -> None:
        if isinstance(event, UserJoinedLobbyEvent):
            await self._publish_user_joined_lobby(event)

        elif isinstance(event, UserLeftLobbyEvent):
            await self._publish_user_left_lobby(event)

    async def _publish_user_joined_lobby(
        self,
        event: UserJoinedLobbyEvent,
    ) -> None:
        event_as_dict = {
            "type": "user_joined",
            "user_id": event.user_id.hex,
        }
        await self._publish(
            channel=self._lobby_channel_factory(event.lobby_id),
            data=event_as_dict,  # type: ignore
        )

    async def _publish_user_left_lobby(
        self,
        event: UserLeftLobbyEvent,
    ) -> None:
        event_as_dict = {
            "type": "user_left",
            "user_id": event.user_id.hex,
        }
        if event.new_admin_id:
            event_as_dict["new_admin_id"] = event.new_admin_id.hex

        await self._publish(
            channel=self._lobby_channel_factory(event.lobby_id),
            data=event_as_dict,  # type: ignore
        )

    def _lobby_channel_factory(self, lobby_id: LobbyId) -> str:
        return f"lobby:{lobby_id.hex}"

    async def _publish(
        self,
        *,
        channel: str,
        data: _Serializable,
    ) -> None:
        await self._send_request(
            method="publish",
            payload={"channel": channel, "data": data},
        )

    async def _send_request(
        self,
        *,
        method: str,
        payload: _Serializable,
    ) -> None:
        response = await self._httpx_client.post(
            url=urljoin(self._config.url, method),
            json=payload,
            headers={"Authorization": f"apikey {self._config.api_key}"},
        )
        response.raise_for_status()
