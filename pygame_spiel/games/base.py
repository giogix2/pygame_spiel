import abc
import pygame
import pyspiel
import typing as t
from pathlib import Path
import numpy as np

from pygame_spiel.games.settings import SCREEN_SIZE


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

        # Get the package directory (works for both editable and regular installs)
        self._package_path = Path(__file__).parent.parent
        self._registered_bots = []

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
        raise NotImplementedError("Subclasses must implement the play() method")

    def _init_bot(
        self,
        bot_type: str,
        game: pyspiel.Game,
        player_id: int,
    ) -> None:
        """
        Returns a bot of type bot_type for the player specified by player_id.

        Parameters:
            bot_type (str): Bot type (mcts, random or human)
            game (pyspiel.Game): open_spiel game
            player_id (int): id of the player that the bot will be driving

        Returns:
            None
        """
        if bot_type not in list(self._registered_bots.keys()) + [
            "mcts",
            "random",
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

        if bot_type == "human":
            return human.HumanBot()

        return self._registered_bots[bot_type](game=game, player_id=player_id)

    def set_bots(self, bot1_type: str, bot2_type: str) -> None:
        """
        Set a Bot for each player. Available bots are: random, human, mcts.
        Only 2-players game currently supported (so only two bots are set)

        Parameters:
            bot1_type (str): Bot type of player 0
            bot2_type (str): Bot type of player 1
        """
        self._bots = []

        for i, bot_type in enumerate([bot1_type, bot2_type]):
            bot = self._init_bot(bot_type, self._game, player_id=i)
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
