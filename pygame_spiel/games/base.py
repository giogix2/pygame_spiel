import abc
import pygame
try:
    import pyspiel
except ImportError as exc:
    raise ImportError("Install pygame_spiel[spiel] or provide a compatible local OpenSpiel 1.3 build") from exc
import typing as t
import numpy as np

from pygame_spiel.games.settings import SCREEN_SIZE
from pygame_spiel.resources import ModelPaths, asset, user_path
from pygame_spiel.bots import dqn

from open_spiel.python.bots import uniform_random, human
from open_spiel.python.algorithms import mcts


class Game(metaclass=abc.ABCMeta):
    def __init__(self, name, current_player):
        self._name = name
        self._current_player = current_player

        #  Initialise game
        self._game = pyspiel.load_game(name)
        self._state = self._game.new_initial_state()
        self._state_string = self._state.to_string()
        pygame.init()

        self._screen = pygame.display.set_mode(SCREEN_SIZE[name])
        pygame.display.set_caption(name)

        self._registered_bots = []

    def _load_image(self, name):
        with asset(name).open("rb") as stream:
            return pygame.image.load(stream, name).convert_alpha()

    @abc.abstractmethod
    def play(
        self, mouse_pos: t.Tuple[int, int], mouse_pressed: t.Tuple[bool, bool, bool]
    ) -> None:
        """
        Abstract interface of the function play(). At each iteration, it requires the mouse position
        and state (which button was pressed, if any).

        Parameters:
            mouse_pos (tuple): Position of the mouse (X,Y coordinates)
            mouse_pressed (tuple): 1 if the i-th button is pressed
        """

    def _init_bot(
        self,
        bot_type: str,
        game: pyspiel.Game,
        player_id: int,
        breakpoint_dir: str = None,
    ) -> None:
        """
        Returns a bot of type bot_type for the player specified by player_id.

        Parameters:
            bot_type (str): Bot type (mcts, random or dqn)
            game (pyspiel.Game): open_spiel game
            player_id (int): id of the player that the bot will be driving
            breakpoint_dir (str): Path to the DQN weigths (optional)

        Returns:
            None
        """
        if bot_type not in list(self._registered_bots.keys()) + [
            "mcts",
            "random",
            "dqn",
            "human",
        ]:
            ValueError("Invalid bot type: %s" % bot_type)
        rng = np.random.RandomState(42)
        if bot_type == "mcts":
            utc = 2  # UCT's exploration constant
            max_simulations = 1000
            rollout_count = 1
            evaluator = mcts.RandomRolloutEvaluator(rollout_count, rng)
            solve = True  # Whether to use MCTS-Solver.
            verbose = False
            bot = mcts.MCTSBot(
                game,
                utc,
                max_simulations,
                evaluator,
                random_state=rng,
                solve=solve,
                verbose=verbose,
            )
            return bot
        if bot_type == "random":
            bot = uniform_random.UniformRandomBot(1, rng)
            return bot
        if bot_type == "dqn":
            # We need to load bots for both players, because the models have been trained
            # using the script breakthrough_dqn.py, causing the issue reported in
            # https://github.com/deepmind/open_spiel/issues/1104.
            # Only the Bot related to the specified player is returned.
            bot0 = dqn.DQNBot(game, player_id=0, checkpoint_dir=breakpoint_dir)
            bot1 = dqn.DQNBot(game, player_id=1, checkpoint_dir=breakpoint_dir)
            return bot0 if player_id == 0 else bot1
        if bot_type == "human":
            return human.HumanBot()

        return self._registered_bots[bot_type](game=game, player_id=player_id)

    def set_bots(
        self, bot1_type: str, bot1_params: str, bot2_type: str, bot2_params: str
    ) -> None:
        """
        Set a Bot for each player. Available bots are: random, human, mcts, dqn.
        Only 2-players game currently supported (so only two bots are set)

        Parameters:
            bot1_type (str): Bot type of player 0
            bot1_params (str): Bot's parameters (e.g., neural network breakpoints)
            bot2_type (str): Bot type of player 1
            bot2_params (str): Bot's parameters (e.g., neural network breakpoints)
        """
        self._bots = []

        for i, (bot_type, params) in enumerate([(bot1_type, bot1_params), (bot2_type, bot2_params)]):
            bot_breakpoint_dir = None
            if bot_type == "dqn":
                if self._name != "breakthrough":
                    raise ValueError("DQN is supported only for Breakthrough")
                bot_breakpoint_dir = user_path(params) if params is not None else ModelPaths().breakthrough_dqn()
                if not bot_breakpoint_dir.is_dir():
                    raise FileNotFoundError(
                        f"DQN checkpoint directory missing: {bot_breakpoint_dir}. "
                        "Prepare it with python -m pygame_spiel.downloads breakthrough"
                    )
            bot = self._init_bot(
                bot_type, self._game, player_id=i, breakpoint_dir=bot_breakpoint_dir
            )
            self._bots.append(bot)

    def register_bots(self, registered_bots: dict[str, type]):
        """
        Register a new Bot class definition.
        This is a class which is loaded at runtime from the pygame_spiel menu.

        Parameters:
            registered_bots (dict[str, type]): dictionary with class names
            and definitions
        """
        self._registered_bots = registered_bots
