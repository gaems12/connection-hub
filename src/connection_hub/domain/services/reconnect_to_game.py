# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = ("ReconnectToGame",)

from uuid import uuid4

from connection_hub.domain.identitifiers import UserId, PlayerStateId
from connection_hub.domain.constants import PlayerStatus
from connection_hub.domain.models import Game
from connection_hub.domain.exceptions import UserIsConnectedToGameError


class ReconnectToGame:
    def __call__(self, *, game: Game, user_id: UserId) -> None:
        player_state = game.players[user_id]

        if player_state.status == PlayerStatus.CONNECTED:
            raise UserIsConnectedToGameError()

        player_state.id = PlayerStateId(uuid4())
        player_state.status = PlayerStatus.CONNECTED
