# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

import json
from typing import Final

from nats.js.client import JetStreamContext

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
from connection_hub.infrastructure.common_retort import CommonRetort


_STREAM: Final = "games"

_EVENT_TO_SUBJECT_MAP: Final = {
    LobbyCreatedEvent: "connection_hub.lobby.created",
    UserJoinedLobbyEvent: "connection_hub.lobby.user_joined",
    UserLeftLobbyEvent: "connection_hub.lobby.user_left",
    ConnectFourGameCreatedEvent: "connection_hub.game.created",
    PlayerDisconnectedEvent: "connection_hub.game.player_disconnected",
    PlayerReconnectedEvent: "connection_hub.game.player_reconnected",
    PlayerDisqualifiedEvent: "connection_hub.game.player_disqualified",
}


class NATSEventPublisher:
    __all__ = ("_jetstream", "_common_retort")

    def __init__(
        self,
        jetstream: JetStreamContext,
        common_retort: CommonRetort,
    ):
        self._jetstream = jetstream
        self._common_retort = common_retort

    async def publish(self, event: Event) -> None:
        subject = _EVENT_TO_SUBJECT_MAP[type(event)]

        event_as_dict = self._common_retort.dump(event)
        payload = json.dumps(event_as_dict).encode()

        await self._jetstream.publish(
            subject=subject,
            payload=payload,
            stream=_STREAM,
        )
