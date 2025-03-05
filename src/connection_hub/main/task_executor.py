# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from taskiq import AsyncBroker
from dishka import AsyncContainer
from dishka.integrations.taskiq import setup_dishka

from connection_hub.infrastructure import load_nats_config
from connection_hub.presentation.task_executor import (
    create_broker,
    ioc_container_factory,
)


def create_task_executor_app(
    *,
    broker: AsyncBroker | None = None,
    ioc_container: AsyncContainer | None = None,
) -> AsyncBroker:
    if not broker:
        nats_config = load_nats_config()
        broker = create_broker(nats_config.url)

    ioc_container = ioc_container or ioc_container_factory()
    setup_dishka(ioc_container, broker)

    return broker


task_executor = create_task_executor_app()
