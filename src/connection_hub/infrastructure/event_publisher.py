# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

__all__ = ("RealEventPublisher",)

import asyncio

from connection_hub.application import Event, EventPublisher
from .message_broker import NATSEventPublisher
from .clients import HTTPXCentrifugoClient


class RealEventPublisher(EventPublisher):
    __slots__ = (
        "_nats_event_publisher",
        "_centrifugo_client",
    )

    def __init__(
        self,
        nats_event_publisher: NATSEventPublisher,
        centrifugo_client: HTTPXCentrifugoClient,
    ):
        self._nats_event_publisher = nats_event_publisher
        self._centrifugo_client = centrifugo_client

    async def publish(self, event: Event) -> None:
        await asyncio.gather(
            self._nats_event_publisher.publish(event),
            self._centrifugo_client.publish_event(event),
            return_exceptions=True,
        )
