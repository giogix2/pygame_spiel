import pyspiel


class Dummy(pyspiel.Bot):
    def __init__(self, game, player_id):
        pyspiel.Bot.__init__(self)
        self._player_id = player_id

    def step(self, state):
        legal_actions = state.legal_actions(self._player_id)
        if not legal_actions:
            return [], pyspiel.INVALID_ACTION
        action = legal_actions[0]  # Always choose 1st action
        return action
