# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from uuid import uuid4

from connection_hub.domain.identitifiers import UserId, PlayerStateId
from connection_hub.domain.constants import PlayerStatus
from connection_hub.domain.models import Game
from connection_hub.domain.exceptions import PlayerIsConnectedError


class ReconnectToGame:
    def __call__(
        self,
        *,
        game: Game,
        current_user_id: UserId,
    ) -> None:
        if current_user_id not in game.players:
            raise Exception(
                "Cannot disconnect from game: player is not in the game.",
            )

        current_player_state = game.players[current_user_id]

        if current_player_state.status == PlayerStatus.CONNECTED:
            raise PlayerIsConnectedError()

        current_player_state.id = PlayerStateId(uuid4())
        current_player_state.status = PlayerStatus.CONNECTED
