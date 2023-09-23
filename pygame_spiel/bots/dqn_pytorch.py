import os
import tensorflow.compat.v1 as tf

from open_spiel.python import rl_environment
from open_spiel.python.pytorch import dqn as dqn_pt

import pyspiel


class DQNBot(pyspiel.Bot):
    """Bot that uses DQN algorithm."""

    def __init__(
        self,
        game,
        player_id,
        replay_buffer_capacity=int(1e5),
        batch_size=32,
        checkpoint_dir=None,
    ):
        """Initializes a DQN algorithm in the form of a bot.
        Args:
          game: A pyspiel.Game to play.
          player_id: ID associated to the player.
          replay_buffer_capacity: Replay buffer size
          batch_size: Training batch size (not used in this Bot yet)
        """

        pyspiel.Bot.__init__(self)

        self._num_players = game.num_players()
        self._hidden_layer_sizes = [64, 64]  # TODO add parameter in constructor
        self._env = rl_environment.Environment(game)
        info_state_size = self._env.observation_spec()["info_state"][0]
        num_actions = self._env.action_spec()["num_actions"]
        self._time_step = self._env.reset()

        self._sess = tf.Session()
        hidden_layers_sizes = [int(l) for l in self._hidden_layer_sizes]

        self._agent = dqn_pt.DQN(
            player_id=player_id,
            state_representation_size=info_state_size,
            num_actions=num_actions,
            hidden_layers_sizes=hidden_layers_sizes,
            replay_buffer_capacity=replay_buffer_capacity,
            batch_size=batch_size,
        )
        # self._agent.restore(checkpoint_dir)
        if checkpoint_dir is not None:
            if not os.path.exists(checkpoint_dir):
                raise FileNotFoundError("No folder exists at the location specified")
            self._agent.restore(checkpoint_dir)
        else:
            self._sess.run(tf.global_variables_initializer())

    def restart_at(self, state):
        pass

    def step(self, state):
        """Returns bot's action at given state."""

        #  Next lines taken from https://github.com/deepmind/open_spiel/issues/896
        player_id = state.current_player()
        legal_actions = [
            state.legal_actions(player_id) for _ in range(self._num_players)
        ]
        info_state = [
            state.observation_tensor(player_id) for _ in range(self._num_players)
        ]
        step_type = (
            rl_environment.StepType.LAST
            if state.is_terminal()
            else rl_environment.StepType.MID
        )
        time_step = rl_environment.TimeStep(
            observations={
                "info_state": info_state,
                "legal_actions": legal_actions,
                "current_player": player_id,
            },
            rewards=state.rewards(),
            discounts=[1.0, 1.0],
            step_type=step_type,
        )

        agent_output = self._agent.step(time_step, is_evaluation=True)
        action = (
            agent_output.action
        )  # TODO expand functionality to simultaneous games with apply_actions()
        return action
