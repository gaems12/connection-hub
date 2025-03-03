# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator

import pytest
from nats.js import JetStreamContext
from uuid_extensions import uuid7

from connection_hub.domain import GameId, LobbyId, UserId, ConnectFourRuleSet
from connection_hub.application import (
    LobbyCreatedEvent,
    UserJoinedLobbyEvent,
    UserLeftLobbyEvent,
    ConnectFourGameCreatedEvent,
    ConnectFourGamePlayerDisconnectedEvent,
    ConnectFourGamePlayerReconnectedEvent,
    ConnectFourGamePlayerDisqualifiedEvent,
    Event,
)
from connection_hub.infrastructure import (
    common_retort_factory,
    NATSConfig,
    nats_client_factory,
    nats_jetstream_factory,
    NATSEventPublisher,
)


@pytest.fixture(scope="function")
async def nats_jetstream(
    nats_config: NATSConfig,
) -> AsyncGenerator[JetStreamContext, None]:
    async for nats_client in nats_client_factory(nats_config):
        yield nats_jetstream_factory(nats_client)


@pytest.mark.parametrize(
    "event",
    [
        LobbyCreatedEvent(
            lobby_id=LobbyId(uuid7()),
            name="Connect Four Game For Money!!!",
            admin_id=UserId(uuid7()),
            has_password=False,
            rule_set=ConnectFourRuleSet(
                time_for_each_player=timedelta(minutes=1),
            ),
        ),
        UserJoinedLobbyEvent(
            lobby_id=LobbyId(uuid7()),
            user_id=UserId(uuid7()),
        ),
        UserLeftLobbyEvent(
            lobby_id=LobbyId(uuid7()),
            user_id=UserId(uuid7()),
            new_admin_id=None,
        ),
        ConnectFourGameCreatedEvent(
            game_id=GameId(uuid7()),
            lobby_id=LobbyId(uuid7()),
            first_player_id=UserId(uuid7()),
            second_player_id=UserId(uuid7()),
            time_for_each_player=timedelta(minutes=1),
            created_at=datetime.now(timezone.utc),
        ),
        ConnectFourGamePlayerDisconnectedEvent(
            game_id=GameId(uuid7()),
            player_id=UserId(uuid7()),
        ),
        ConnectFourGamePlayerReconnectedEvent(
            game_id=GameId(uuid7()),
            player_id=UserId(uuid7()),
        ),
        ConnectFourGamePlayerDisqualifiedEvent(
            game_id=GameId(uuid7()),
            player_id=UserId(uuid7()),
        ),
    ],
)
async def test_nats_event_publihser(
    event: Event,
    nats_jetstream: JetStreamContext,
):
    event_publisher = NATSEventPublisher(
        jetstream=nats_jetstream,
        common_retort=common_retort_factory(),
    )
    await event_publisher.publish(event)
