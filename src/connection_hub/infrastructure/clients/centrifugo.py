# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from urllib.parse import urljoin
from dataclasses import dataclass

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
    PlayerDisconnectedEvent,
    PlayerReconnectedEvent,
    PlayerDisqualifiedEvent,
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
        if isinstance(event, LobbyCreatedEvent):
            await self._publish_lobby_created(event)

        elif isinstance(event, UserJoinedLobbyEvent):
            await self._publish_user_joined_lobby(event)

        elif isinstance(event, UserLeftLobbyEvent):
            await self._publish_user_left_lobby(event)

        elif isinstance(event, ConnectFourGameCreatedEvent):
            await self._publish_connect_four_game_created(event)

        elif isinstance(event, PlayerDisconnectedEvent):
            await self._publish_player_disconnected(event)

        elif isinstance(event, PlayerReconnectedEvent):
            await self._publish_player_reconnected(event)

        elif isinstance(event, PlayerDisqualifiedEvent):
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
        event: PlayerDisconnectedEvent,
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
        event: PlayerReconnectedEvent,
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
        event: PlayerDisqualifiedEvent,
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
