import abc
import pygame
import pyspiel
import typing as t
import site
from pathlib import Path
import os

from pygame_spiel.games.settings import SCREEN_SIZE, BREAKPOINTS_DRIVE_IDS
from pygame_spiel.utils import init_bot, download_weights


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

        self._package_path = site.getsitepackages()[0]

    @abc.abstractmethod
    def play(
        self, mouse_pos: t.Tuple[int, int], mouse_pressed: t.Tuple[bool, bool, bool]
    ) -> None:
        """
        Abstact interface of the function play(). At each iteration, it requires the mouse position
        and state (which button was pressed, if any).

        Parameters:
            mouse_pos (tuple): Position of the mouse (X,Y coordinates)
            mouse_pressed (tuple): 1 if the i-th button is pressed
        """

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
        # TODO self._bot_params is not used. Remove

        self._bot_params = [bot1_params, bot2_params]
        self._bots = []

        for i, bot_type in enumerate([bot1_type, bot2_type]):
            bot_breakpoint_dir = None
            if bot_type in ["dqn"]:
                breakpoint_dest_dir = Path(
                    self._package_path,
                    "pygame_spiel/data/breakpoints",
                    bot_type,
                    self._name,
                )
                file_id = BREAKPOINTS_DRIVE_IDS[self._name][bot_type]
                print(breakpoint_dest_dir)
                if not os.path.exists(breakpoint_dest_dir):
                    print(
                        f"Downloading breakpoints for bot {bot_type} and game {self._name}"
                    )
                    download_weights(
                        file_id=file_id, dest_folder=str(breakpoint_dest_dir)
                    )
                bot_breakpoint_dir = Path(breakpoint_dest_dir, "weights_default")
            bot = init_bot(
                bot_type, self._game, player_id=i, breakpoint_dir=bot_breakpoint_dir
            )
            self._bots.append(bot)
