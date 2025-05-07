# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from typing import Protocol

from connection_hub.domain import LobbyId, UserId, Lobby


class LobbyGateway(Protocol):
    async def by_id(
        self,
        lobby_id: LobbyId,
        *,
        acquire: bool = False,
    ) -> Lobby | None:
        """
        Returns lobby by specified `lobby_id`.

        Parameters:

            `acquire`: Locks the returned lobby, preventing it from
                being accessed via methods with this flag until
                the current transaction is completed.
        """
        raise NotImplementedError

    async def by_user_id(
        self,
        user_id: UserId,
        *,
        acquire: bool = False,
    ) -> Lobby | None:
        """
        Returns lobby by specified `user_id`.

        Parameters:

            `acquire`: Locks the returned lobby, preventing it from
                being accessed via methods with this flag until
                the current transaction is completed.
        """
        raise NotImplementedError

    async def save(self, lobby: Lobby) -> None:
        raise NotImplementedError

    async def update(self, lobby: Lobby) -> None:
        raise NotImplementedError

    async def delete(self, lobby: Lobby) -> None:
        raise NotImplementedError
