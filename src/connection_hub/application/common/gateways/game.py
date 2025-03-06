# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from typing import Protocol

from connection_hub.domain import UserId, GameId, Game


class GameGateway(Protocol):
    async def by_id(
        self,
        id: GameId,
        *,
        acquire: bool = False,
    ) -> Game | None:
        """
        Returns game by specified `game_id`.

        Parameters:

            `acquire`: Locks the returned game, preventing it from
                being accessed via methods with this flag until
                the current transaction is completed.
        """
        raise NotImplementedError

    async def by_player_id(
        self,
        player_id: UserId,
        *,
        acquire: bool = False,
    ) -> Game | None:
        """
        Returns game by specified `player_id`.

        Parameters:

            `acquire`: Locks the returned game, preventing it from
                being accessed via methods with this flag until
                the current transaction is completed.
        """
        raise NotImplementedError

    async def save(self, game: Game) -> None:
        raise NotImplementedError

    async def update(self, game: Game) -> None:
        raise NotImplementedError

    async def delete(self, game: Game) -> None:
        raise NotImplementedError
