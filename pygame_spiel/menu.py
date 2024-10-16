import os
import typing as t
from pathlib import Path
import pygame
import pygame_menu
from pygame_menu import themes

from pygame_spiel.games.settings import GAMES_BOTS
from pygame_spiel.utils import register_classes


class Menu:
    def __init__(self):
        pygame.init()
        self._menu_surface = pygame.display.set_mode([600, 600])
        pygame.display.set_caption("Pygame Open Spiel")

        self._selected_game = "breakthrough"
        self._selected_opponent_type = "mcts"
        self._list_opponent_types = self._get_game_available_bots(self._selected_game)
        self._list_opponents = [
            (opp_type, i) for i, opp_type in enumerate(self._list_opponent_types)
        ]
        self._current_path = os.getcwd()
        self._bot_path = None
        self._registered_bots = dict()

        self._mainmenu = pygame_menu.Menu(
            "Pygame spiel", 600, 600, theme=themes.THEME_SOLARIZED
        )

        self._menu_dropselect_module = self._mainmenu.add.dropselect(
            "Module (optional) :",
            items=self._get_files_and_folders(self._current_path),
            onchange=self._select_module,
        )
        self._mainmenu.add.label("", label_id="path_display", max_char=-1, font_size=20)
        self._menu_dropselect_game = self._mainmenu.add.dropselect(
            "Game :",
            [("breakthrough", 1), ("tic_tac_toe", 2)],
            onchange=self._select_game,
            default=0,
        )
        self._menu_dropselect_opponent = self._mainmenu.add.dropselect(
            "Opponent :",
            self._list_opponents,
            onchange=self._select_opponent,
            default=0,
        )
        self._mainmenu.add.button("Play", self._start_game)

    def display(
        self,
    ):
        """Run the Pygame display function which visualizes the menu on screen."""
        self._mainmenu.mainloop(self._menu_surface)

    def _get_files_and_folders(self, path: str = ".") -> list[tuple[str, str]]:
        """
        Returns a list of files and folders in a given directory.
        The returned list is visualized in the main menu. The list contains
        repeating values (e.g., (item, item)), which though have redundant
        information, it's the supported format in Pygame-menu droplists.

        Parameters:
            path (str): directory path from which to get the list of files

        Returns:
            list[tuple[str, str]]: list containing files and folder names
        """
        items = [".."]  # Add option to go up one directory
        items.extend(sorted(os.listdir(path)))
        return [(item, item) for item in items]

    def _update_modules_dropdown(self):
        """Helper function to visualize new information in the modules dropdown."""
        items = self._get_files_and_folders(self._current_path)
        self._menu_dropselect_module.update_items(items)

    def _select_module(self, selected_value: tuple[tuple[str, str], int], *args):
        """
        Callback function for the Dropselect menu used to select modules.

        Parameters:
            selected_value (tuple): module name and position in the dropdown
        """
        selected_item = selected_value[0][0]
        self._bot_path = None
        self._mainmenu.get_widget("path_display").set_title("")

        if selected_item == "..":
            self._current_path = os.path.dirname(self._current_path)
        else:
            new_path = os.path.join(self._current_path, selected_item)
            if os.path.isdir(new_path):
                self._current_path = new_path
            if new_path.endswith(".py"):
                self._bot_path = new_path
                file_name = Path(new_path).name
                self._registered_bots = register_classes(file_path=self._bot_path)
                for class_name in self._registered_bots.keys():
                    self._list_opponents.append((class_name, class_name))
                self._menu_dropselect_opponent.update_items(self._list_opponents)
                str_registered_bots = ", ".join(self._registered_bots.keys())
                self._mainmenu.get_widget("path_display").set_title(
                    f"Selected file: {file_name} (new Bots: {str_registered_bots})"
                )
        self._update_modules_dropdown()

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
        Callback function for the Dropselect menu used to select the opponent's Bot type.

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
        Getter which returns the current selected opponent's Bot type.

        Returns:
            selected_opponent_type (str): opponent's type selected in the menu
        """
        return self._selected_opponent_type

    def get_selected_bot_file(self) -> str:
        """
        Getter which returns path to a file containing a new Bot definition.

        Returns:
            bot_path (str): path to a .py file containing a Bot definition
        """
        return self._bot_path

    def get_registered_bots(self) -> dict:
        """
        Getter which returns the bots registered from custom modules.

        Returns:
            registered_bots (dict): dictionary with {class name: class} for each registered Bot
        """
        return self._registered_bots
