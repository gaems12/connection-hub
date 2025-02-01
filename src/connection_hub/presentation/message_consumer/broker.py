# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from faststream.nats import NatsBroker

from .routes import router


def create_broker(nats_url: str) -> NatsBroker:
    broker = NatsBroker((nats_url,))

    broker.include_router(router)

    return broker
