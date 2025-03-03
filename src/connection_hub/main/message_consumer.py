# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from importlib.metadata import version

from faststream import FastStream
from faststream.nats import NatsBroker
from dishka import AsyncContainer
from dishka.integrations.faststream import setup_dishka

from connection_hub.infrastructure import load_nats_config
from connection_hub.presentation.message_consumer import (
    create_broker,
    ioc_container_factory,
)


def create_message_consumer_app(
    *,
    broker: NatsBroker | None = None,
    ioc_container: AsyncContainer | None = None,
) -> FastStream:
    if not broker:
        nats_config = load_nats_config()
        broker = create_broker(nats_config.url)

    app = FastStream(
        broker=broker,
        title="Connection Hub",
        version=version("connection_hub"),
    )
    ioc_container = ioc_container or ioc_container_factory()
    setup_dishka(ioc_container, app)

    return app
