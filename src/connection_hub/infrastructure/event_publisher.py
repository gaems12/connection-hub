# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

__all__ = ("RealEventPublisher",)

from connection_hub.application import Event, EventPublisher
from .message_broker import NATSEventPublisher


class RealEventPublisher(EventPublisher):
    __slots__ = ("_nats_event_publisher",)

    def __init__(self, nats_event_publisher: NATSEventPublisher):
        self._nats_event_publisher = nats_event_publisher

    async def publish(self, event: Event) -> None:
        await self._nats_event_publisher.publish(event)
