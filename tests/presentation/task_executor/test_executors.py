# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from unittest.mock import AsyncMock

import pytest
from taskiq import TaskiqMessage, InMemoryBroker
from taskiq.formatters.proxy_formatter import ProxyFormatter
from dishka import Provider, Scope, AsyncContainer, make_async_container
from dishka.integrations.taskiq import TaskiqProvider, setup_dishka
from uuid_extensions import uuid7

from connection_hub.domain import GameId, UserId, PlayerStateId
from connection_hub.application import (
    TryToDisqualifyPlayerCommand,
    TryToDisqualifyPlayerProcessor,
)
from connection_hub.infrastructure import OperationId
from connection_hub.presentation.task_executor import create_broker


@pytest.fixture(scope="function")
def ioc_container() -> AsyncContainer:
    provider = Provider()

    provider.provide(
        lambda: AsyncMock(),
        scope=Scope.REQUEST,
        provides=TryToDisqualifyPlayerProcessor,
    )

    return make_async_container(provider, TaskiqProvider())


@pytest.fixture(scope="function")
async def app(ioc_container: AsyncContainer) -> InMemoryBroker:
    broker = create_broker()
    setup_dishka(ioc_container, broker)

    await broker.startup()

    return broker


async def test_try_to_disqualify_player(app: InMemoryBroker) -> None:
    taskiq_message = TaskiqMessage(
        task_id=uuid7().hex,
        task_name="try_to_disqualify_player",
        labels={},
        labels_types=None,
        args=[OperationId(uuid7())],
        kwargs={
            "command": TryToDisqualifyPlayerCommand(
                game_id=GameId(uuid7()),
                player_id=UserId(uuid7()),
                player_state_id=PlayerStateId(uuid7()),
            ),
        },
    )

    proxy_formatter = ProxyFormatter(app)
    broker_message = proxy_formatter.dumps(taskiq_message)

    await app.kick(broker_message)
