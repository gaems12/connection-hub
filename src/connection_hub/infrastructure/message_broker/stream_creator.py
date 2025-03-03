# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from nats.js import JetStreamContext
from nats.js.api import StreamConfig


class NATSStreamCreator:
    __slots__ = ("_jetstream",)

    def __init__(self, jetstream: JetStreamContext):
        self._jetstream = jetstream

    async def create(self) -> None:
        games_stream_config = StreamConfig(
            name="games",
            subjects=[
                "connection_hub.lobby.created",
                "connection_hub.lobby.user_joined",
                "connection_hub.lobby.user_left",
                "connection_hub.game.created",
                "connection_hub.connect_four.game.player_disconnected",
                "connection_hub.connect_four.game.player_reconnected",
                "connection_hub.connect_four.game.player_disqualified",
                "api_gateway.lobby.created",
                "api_gateway.lobby.user_joined",
                "api_gateway.lobby.user_left",
                "api_gateway.game.created",
                "api_gateway.game.player_disconnected",
                "api_gateway.game.player_reconnected",
                "connect_four.game.ended",
            ],
        )
        await self._jetstream.add_stream(games_stream_config)
