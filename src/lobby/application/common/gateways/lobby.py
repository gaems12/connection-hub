# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from typing import Protocol

from lobby.domain import LobbyId, UserId, Lobby


class LobbyGateway(Protocol):
    async def by_id(
        self,
        id: LobbyId,
        *,
        acquire: bool = False,
    ) -> Lobby | None:
        """
        Returns lobby by specified `id`.

        Parameters:

            `acquire`: Locks the returned lobby, preventing it from
                being accessed via this method with this flag until
                the current transaction is completed.
        """
        raise NotImplementedError

    async def by_user_id(self, user_id: UserId) -> Lobby | None:
        raise NotImplementedError

    async def save(self, lobby: Lobby) -> None:
        raise NotImplementedError

    async def update(self, lobby: Lobby) -> None:
        raise NotImplementedError
