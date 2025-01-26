# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from connection_hub.domain.identitifiers import UserId
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
        if current_user_id not in game.players:
            raise Exception(
                "DisconnectFromGame. Cannot disconnect from game: "
                "player is not in the game.",
            )

        if game.players[current_user_id].status == PlayerStatus.DISCONNECTED:
            raise PlayerIsDisconnectedError()

        game.players[current_user_id].status = PlayerStatus.DISCONNECTED
