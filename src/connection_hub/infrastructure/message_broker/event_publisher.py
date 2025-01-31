# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

import json
from typing import Final

from nats.js.client import JetStreamContext

from connection_hub.application import (
    LobbyCreatedEvent,
    UserJoinedLobbyEvent,
    UserLeftLobbyEvent,
    FourInARowGameCreatedEvent,
    PlayerWasDisqualifiedEvent,
    Event,
)
from connection_hub.infrastructure.common_retort import CommonRetort


_STREAM: Final = "connection_hub"

_EVENT_TO_SUBJECT_MAP: Final = {
    LobbyCreatedEvent: "lobby.created",
    UserJoinedLobbyEvent: "lobby.user_joined",
    UserLeftLobbyEvent: "lobby.user_left",
    FourInARowGameCreatedEvent: "game.created",
    PlayerWasDisqualifiedEvent: "game.player_disqualified",
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

        event_as_dict = self._common_retort.dump(event, dict)
        payload = json.dumps(event_as_dict).encode()

        await self._jetstream.publish(
            subject=subject,
            payload=payload,
            stream=_STREAM,
        )
