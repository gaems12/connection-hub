# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from taskiq import TaskiqScheduler
from taskiq_nats import PullBasedJetStreamBroker
from dishka.integrations.taskiq import setup_dishka

from connection_hub.infrastructure import (
    load_nats_config,
    load_redis_config,
    taskiq_redis_schedule_source_factory,
)
from connection_hub.presentation.task_executor import (
    try_to_disqualify_player,
    ioc_container_factory,
)


def create_task_executor_app() -> TaskiqScheduler:
    nats_config = load_nats_config()
    redis_config = load_redis_config()

    broker = PullBasedJetStreamBroker(
        [nats_config.url],
        pull_consume_timeout=0.2,
    )
    broker.register_task(try_to_disqualify_player)

    ioc_container = ioc_container_factory()
    setup_dishka(ioc_container, broker)

    schedule_source = taskiq_redis_schedule_source_factory(redis_config)
    app = TaskiqScheduler(broker, [schedule_source])

    return app
