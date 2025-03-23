# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from typing import Final

from connection_hub.domain.identitifiers import UserId, PlayerStateId
from connection_hub.domain.models import Game, ConnectFourGame


_GAME_TO_MIN_PLAYERS_MAP: Final = {
    ConnectFourGame: 2,
}


class TryToDisqualifyPlayer:
    def __call__(
        self,
        *,
        game: Game,
        user_id: UserId,
        player_state_id: PlayerStateId,
    ) -> tuple[bool, bool]:
        """
        Disqualifies a player if their current state matches the
        expected one. Returns flags indicating whether the
        disqualification was successful and whether game is ended.
        """
        player_state = game.players[user_id]
        if player_state.id != player_state_id:
            return False, False

        game.players.pop(user_id)
        min_players = _GAME_TO_MIN_PLAYERS_MAP[type(game)]
        is_not_enough_players_to_continue = len(game.players) < min_players

        return True, is_not_enough_players_to_continue
