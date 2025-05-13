# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = ("nats_client_factory", "nats_jetstream_factory")

from typing import AsyncGenerator

from nats.aio.client import Client
from nats.js.client import JetStreamContext

from .config import NATSConfig


async def nats_client_factory(
    config: NATSConfig,
) -> AsyncGenerator[Client, None]:
    client = Client()
    await client.connect([config.url])
    yield client
    await client.close()


def nats_jetstream_factory(nats_client: Client) -> JetStreamContext:
    return nats_client.jetstream()
