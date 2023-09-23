import typing as t
import pygame
import pygame_menu
from pygame_menu import themes

from pygame_spiel.games.settings import GAMES_BOTS


class Menu:
    def __init__(self):
        pygame.init()
        self._menu_surface = pygame.display.set_mode([600, 600])
        pygame.display.set_caption("Pygame Open Spiel")

        self._selected_game = "breakthrough"
        self._selected_opponent_type = "mcts"
        self._list_opponent_types = self._get_game_available_bots(self._selected_game)
        drop_select_items = [
            (opp_type, i) for i, opp_type in enumerate(self._list_opponent_types)
        ]

        self._mainmenu = pygame_menu.Menu(
            "Pygame spiel", 600, 600, theme=themes.THEME_SOLARIZED
        )

        # self._mainmenu.add.text_input('Name: ', default='username', maxchar=20)
        self._menu_dropselect_game = self._mainmenu.add.dropselect(
            "Game :",
            [("breakthrough", 1), ("tic_tac_toe", 2)],
            onchange=self._select_game,
            default=0,
        )
        self._menu_dropselect_opponent = self._mainmenu.add.dropselect(
            "Opponent :", drop_select_items, onchange=self._select_opponent, default=0
        )
        self._mainmenu.add.button("Play", self._start_game)

    def display(
        self,
    ):
        """Run the Pygame display function which visualizes the menu on screen."""
        self._mainmenu.mainloop(self._menu_surface)

    def _get_game_available_bots(self, game: str) -> t.List:
        """
        Returns the list of available bots for a specified game.
        Example: _get_game_available_bots('breaktrhough') -> ['mcts', 'dqn']

        Parameters:
            game (str): selected game
        """
        dict_game_info = GAMES_BOTS[game]
        list_bot_types = list(dict_game_info.keys())
        return list_bot_types

    def _select_game(self, game: str, game_index: int):
        """
        Callback function for the Dropselect menu used to select the game.

        Parameters:
            game (str): game selected in the drop-select menu
            game_index (int): index of the selected game
        """
        self._selected_game = game[0][0]
        self._list_opponent_types = self._get_game_available_bots(self._selected_game)

        drop_select_items = [
            (opp_type, i) for i, opp_type in enumerate(self._list_opponent_types)
        ]
        self._menu_dropselect_opponent.update_items(drop_select_items)

    def _select_opponent(self, bot_type: str, opp_index: int):
        """
        Callback function for the Dropselect menu used to select the opponent's bot type.

        Parameters:
            bot_type (str): opponent type selected in the drop-select menu
            opp_index (int): index of the selected opponent type
        """
        self._selected_opponent_type = bot_type[0][0]

    def _start_game(self):
        """Callback function used when the button Play is selected, which turns off the menu."""
        self._mainmenu.disable()

    def get_selected_game(self) -> str:
        """
        Getter which returns the current selected game.

        Returns:
            selected_game (str): game selected in the menu
        """
        return self._selected_game

    def get_selected_opponent(self) -> str:
        """
        Getter which returns the current selected opponent's bot type.

        Returns:
            selected_opponent_type (str): opponent's type selected in the menu
        """
        return self._selected_opponent_type
