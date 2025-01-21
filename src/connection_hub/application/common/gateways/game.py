# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from typing import Protocol

from connection_hub.domain import UserId, Game


class GameGateway(Protocol):
    async def by_player_id(self, player_id: UserId) -> Game | None:
        raise NotImplementedError
