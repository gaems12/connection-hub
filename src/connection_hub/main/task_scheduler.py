# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from taskiq import TaskiqScheduler
from taskiq_nats import PullBasedJetStreamBroker

from connection_hub.infrastructure import (
    load_nats_config,
    load_redis_config,
    taskiq_redis_schedule_source_factory,
)


def create_task_scheduler_app() -> TaskiqScheduler:
    nats_config = load_nats_config()
    redis_config = load_redis_config()

    broker = PullBasedJetStreamBroker(
        [nats_config.url],
        pull_consume_timeout=0.2,
    )
    schedule_source = taskiq_redis_schedule_source_factory(redis_config)
    app = TaskiqScheduler(broker, [schedule_source])

    return app
