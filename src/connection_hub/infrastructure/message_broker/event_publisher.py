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
    UserRemovedFromLobbyEvent,
    UserKickedFromLobbyEvent,
    ConnectFourGameCreatedEvent,
    ConnectFourGamePlayerDisconnectedEvent,
    ConnectFourGamePlayerReconnectedEvent,
    ConnectFourGamePlayerDisqualifiedEvent,
    Event,
)
from connection_hub.infrastructure.common_retort import CommonRetort
from connection_hub.infrastructure.operation_id import OperationId


_STREAM: Final = "games"

_EVENT_TO_SUBJECT_MAP: Final = {
    LobbyCreatedEvent: "connection_hub.lobby.created",
    UserJoinedLobbyEvent: "connection_hub.lobby.user_joined",
    UserLeftLobbyEvent: "connection_hub.lobby.user_left",
    UserRemovedFromLobbyEvent: "connection_hub.lobby.user_removed",
    UserKickedFromLobbyEvent: "connection_hub.lobby.user_kicked",
    ConnectFourGameCreatedEvent: "connection_hub.connect_four.game.created",
    ConnectFourGamePlayerDisconnectedEvent: (
        "connection_hub.connect_four.game.player_disconnected"
    ),
    ConnectFourGamePlayerReconnectedEvent: (
        "connection_hub.connect_four.game.player_reconnected"
    ),
    ConnectFourGamePlayerDisqualifiedEvent: (
        "connection_hub.connect_four.game.player_disqualified"
    ),
}


class NATSEventPublisher:
    __all__ = ("_jetstream", "_common_retort", "_operation_id")

    def __init__(
        self,
        jetstream: JetStreamContext,
        common_retort: CommonRetort,
        operation_id: OperationId,
    ):
        self._jetstream = jetstream
        self._common_retort = common_retort
        self._operation_id = operation_id

    async def publish(self, event: Event) -> None:
        subject = _EVENT_TO_SUBJECT_MAP[type(event)]

        event_as_dict = self._common_retort.dump(event)
        event_as_dict["operation_id"] = str(self._operation_id)
        payload = json.dumps(event_as_dict).encode()

        await self._jetstream.publish(
            subject=subject,
            payload=payload,
            stream=_STREAM,
        )
