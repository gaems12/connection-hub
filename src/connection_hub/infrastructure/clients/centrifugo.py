# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

import asyncio
import random
import logging
from urllib.parse import urljoin
from dataclasses import dataclass
from typing import Final

from httpx import AsyncClient

from connection_hub.domain import (
    LobbyId,
    GameId,
    UserId,
    ConnectFourRuleSet,
)
from connection_hub.application import (
    LobbyCreatedEvent,
    UserJoinedLobbyEvent,
    UserLeftLobbyEvent,
    ConnectFourGameCreatedEvent,
    ConnectFourGamePlayerDisconnectedEvent,
    ConnectFourGamePlayerReconnectedEvent,
    ConnectFourGamePlayerDisqualifiedEvent,
    Event,
)
from connection_hub.infrastructure.utils import get_env_var


_logger = logging.getLogger(__name__)

_MAX_RETRIES: Final = 20
_BASE_BACKOFF_DELAY: Final = 0.5
_MAX_BACKOFF_DELAY: Final = 10


type _Serializable = (
    str
    | int
    | float
    | bytes
    | None
    | list[_Serializable]
    | dict[str, _Serializable]
)


class CentrifuoClientError(Exception): ...


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
        if isinstance(event, LobbyCreatedEvent):
            await self._publish_lobby_created(event)

        elif isinstance(event, UserJoinedLobbyEvent):
            await self._publish_user_joined_lobby(event)

        elif isinstance(event, UserLeftLobbyEvent):
            await self._publish_user_left_lobby(event)

        elif isinstance(event, ConnectFourGameCreatedEvent):
            await self._publish_connect_four_game_created(event)

        elif isinstance(event, ConnectFourGamePlayerDisconnectedEvent):
            await self._publish_player_disconnected(event)

        elif isinstance(event, ConnectFourGamePlayerReconnectedEvent):
            await self._publish_player_reconnected(event)

        elif isinstance(event, ConnectFourGamePlayerDisqualifiedEvent):
            await self._publish_player_disqualified(event)

    async def _publish_lobby_created(
        self,
        event: LobbyCreatedEvent,
    ) -> None:
        rule_set = event.rule_set

        if isinstance(rule_set, ConnectFourRuleSet):
            rule_set_as_dict = {
                "type": "connect_four",
                "time_for_each_player": (
                    rule_set.time_for_each_player.total_seconds()
                ),
            }

        event_as_dict = {
            "type": "lobby_created",
            "lobby_id": event.lobby_id.hex,
            "name": event.name,
            "rule_set": rule_set_as_dict,
        }
        await self._publish(
            channel=self._user_channel_factory(event.admin_id),
            data=event_as_dict,  # type: ignore
        )

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

    async def _publish_connect_four_game_created(
        self,
        event: ConnectFourGameCreatedEvent,
    ) -> None:
        event_as_dict = {
            "type": "connect_four_game_created",
            "game_id": event.game_id.hex,
            "lobby_id": event.lobby_id.hex,
            "first_player_id": event.first_player_id.hex,
            "second_player_id": event.second_player_id.hex,
            "time_for_each_player": event.time_for_each_player.total_seconds(),
            "created_at": event.created_at.isoformat(),
        }
        await self._publish(
            channel=self._lobby_channel_factory(event.lobby_id),
            data=event_as_dict,  # type: ignore
        )

    async def _publish_player_disconnected(
        self,
        event: ConnectFourGamePlayerDisconnectedEvent,
    ) -> None:
        event_as_dict = {
            "type": "player_disconnected",
            "player_id": event.player_id.hex,
        }
        await self._publish(
            channel=self._game_channel_factory(event.game_id),
            data=event_as_dict,  # type: ignore
        )

    async def _publish_player_reconnected(
        self,
        event: ConnectFourGamePlayerReconnectedEvent,
    ) -> None:
        event_as_dict = {
            "type": "player_reconnected",
            "player_id": event.player_id.hex,
        }
        await self._publish(
            channel=self._game_channel_factory(event.game_id),
            data=event_as_dict,  # type: ignore
        )

    async def _publish_player_disqualified(
        self,
        event: ConnectFourGamePlayerDisqualifiedEvent,
    ) -> None:
        event_as_dict = {
            "type": "player_disqualified",
            "player_id": event.player_id.hex,
        }
        await self._publish(
            channel=self._game_channel_factory(event.game_id),
            data=event_as_dict,  # type: ignore
        )

    def _user_channel_factory(self, user_id: UserId) -> str:
        return f"users:{user_id.hex}"

    def _lobby_channel_factory(self, lobby_id: LobbyId) -> str:
        return f"lobbies:{lobby_id.hex}"

    def _game_channel_factory(self, game_id: GameId) -> str:
        return f"games:{game_id.hex}"

    async def _publish(
        self,
        *,
        channel: str,
        data: _Serializable,
    ) -> None:
        await self._send_request(
            url=urljoin(self._config.url, "publish"),
            json_={"channel": channel, "data": data},
            retry_on_failure=True,
        )

    async def _send_request(
        self,
        *,
        url: str,
        json_: _Serializable,
        retry_on_failure: bool,
    ) -> None:
        try:
            _logger.debug(
                {
                    "message": "Going to make request to centrifugo.",
                    "url": url,
                    "json": json_,
                },
            )
            response = await self._httpx_client.post(
                url=url,
                json=json_,
                headers={"X-API-Key": self._config.api_key},
            )
        except Exception as e:
            error_message = (
                "Unexpected error occurred during request to centrifugo."
            )
            _logger.exception(error_message)

            if retry_on_failure:
                retries_were_successful = await self._retry_request(
                    url=url,
                    json_=json_,
                )
                if retries_were_successful:
                    return

            raise CentrifuoClientError(error_message)

        if response.status_code == 200:
            _logger.debug(
                {
                    "message": "Centrifuo responded.",
                    "status_code": response.status_code,
                    "Centrifuo responded."
                    "content": response.content.decode(),
                },
            )
            return

        error_message = "Centrifugo responded with bad status code."
        _logger.error(
            {
                "message": error_message,
                "status_code": response.status_code,
                "content": response.content.decode(),
            },
        )

        if retry_on_failure:
            retries_were_successful = await self._retry_request(
                url=url,
                json_=json_,
            )
            if retries_were_successful:
                return

        raise CentrifuoClientError(error_message)

    async def _retry_request(
        self,
        *,
        url: str,
        json_: _Serializable,
    ) -> bool:
        for retry_number in range(1, _MAX_RETRIES + 1):
            try:
                _logger.debug(
                    {
                        "message": "Going to retry request to centrifugo.",
                        "retry_number": retry_number,
                        "retries_left": _MAX_RETRIES - retry_number,
                    },
                )
                await self._send_request(
                    url=url,
                    json_=json_,
                    retry_on_failure=False,
                )
                return True

            except CentrifuoClientError:
                if retry_number == _MAX_RETRIES:
                    return False

                wait_time = self._calculate_backoff_wait_time(retry_number)
                await asyncio.sleep(wait_time)

        return False

    def _calculate_backoff_wait_time(self, retry_number: int) -> float:
        return min(
            _BASE_BACKOFF_DELAY * (2**retry_number) + random.uniform(0, 0.5),
            _MAX_BACKOFF_DELAY,
        )
