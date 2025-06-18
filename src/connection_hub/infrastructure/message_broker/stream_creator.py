# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = ("NATSStreamCreator",)

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
                "gaems12.connection_hub.lobby.created",
                "gaems12.connection_hub.lobby.user_joined",
                "gaems12.connection_hub.lobby.user_left",
                "gaems12.connection_hub.lobby.user_removed",
                "gaems12.connection_hub.lobby.user_kicked",
                "gaems12.connection_hub.connect_four.game.created",
                "gaems12.connection_hub.connect_four.game.player_disconnected",
                "gaems12.connection_hub.connect_four.game.player_reconnected",
                "gaems12.connection_hub.connect_four.game.player_disqualified",
                "gaems12.api_gateway.lobby.created",
                "gaems12.api_gateway.lobby.user_joined",
                "gaems12.api_gateway.lobby.user_left",
                "gaems12.api_gateway.lobby.user_kicked",
                "gaems12.api_gateway.game.created",
                "gaems12.api_gateway.game.player_disconnected",
                "gaems12.api_gateway.game.player_reconnected",
                "gaems12.api_gateway.presence.acknowledged",
                "gaems12.connect_four.game.created",
                "gaems12.*.game.ended",
            ],
        )
        await self._jetstream.add_stream(games_stream_config)
