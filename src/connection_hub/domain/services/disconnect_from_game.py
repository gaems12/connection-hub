# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from uuid import uuid4

from connection_hub.domain.identitifiers import UserId, PlayerStateId
from connection_hub.domain.constants import PlayerStatus
from connection_hub.domain.models import Game
from connection_hub.domain.exceptions import PlayerIsDisconnectedError


class DisconnectFromGame:
    def __call__(
        self,
        *,
        game: Game,
        current_user_id: UserId,
    ) -> None:
        current_player_state = game.players[current_user_id]

        if current_player_state.status == PlayerStatus.DISCONNECTED:
            raise PlayerIsDisconnectedError()

        current_player_state.id = PlayerStateId(uuid4())
        current_player_state.status = PlayerStatus.DISCONNECTED
