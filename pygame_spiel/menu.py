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
        # Store selections for both players
        self._selected_player1_type = "human"
        self._selected_player2_type = "mcts"
        self._list_player_types = self._get_game_available_bots_with_human(
            self._selected_game
        )
        self._list_players = [
            (player_type, i) for i, player_type in enumerate(self._list_player_types)
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
        # Create dynamic game list from GAMES_BOTS
        game_items = [
            (game_name, i) for i, game_name in enumerate(GAMES_BOTS.keys(), 1)
        ]
        self._menu_dropselect_game = self._mainmenu.add.dropselect(
            "Game :",
            game_items,
            onchange=self._select_game,
            default=0,
        )
        # Add dropdown for Player 1
        self._menu_dropselect_player1 = self._mainmenu.add.dropselect(
            "Player 1 :",
            self._list_players,
            onchange=lambda selected, *args: self._select_player(1, selected),
            default=0,  # Default to "human"
        )
        # Add dropdown for Player 2
        self._menu_dropselect_player2 = self._mainmenu.add.dropselect(
            "Player 2 :",
            self._list_players,
            onchange=lambda selected, *args: self._select_player(2, selected),
            default=1,  # Default to "mcts" (second item)
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
                    self._list_players.append((class_name, class_name))
                self._menu_dropselect_player1.update_items(self._list_players)
                self._menu_dropselect_player2.update_items(self._list_players)
                str_registered_bots = ", ".join(self._registered_bots.keys())
                self._mainmenu.get_widget("path_display").set_title(
                    f"Selected file: {file_name} (new Bots: {str_registered_bots})"
                )
        self._update_modules_dropdown()

    def _get_game_available_bots(self, game: str) -> t.List:
        """
        Returns the list of available bots for a specified game.
        Example: _get_game_available_bots('breaktrhough') -> ['mcts']

        Parameters:
            game (str): selected game
        """
        dict_game_info = GAMES_BOTS[game]
        list_bot_types = list(dict_game_info.keys())
        return list_bot_types

    def _get_game_available_bots_with_human(self, game: str) -> t.List:
        """
        Returns the list of available bots for a specified game, including "human".
        Example: _get_game_available_bots_with_human('breaktrhough') -> ['human', 'mcts']

        Parameters:
            game (str): selected game
        """
        list_bot_types = self._get_game_available_bots(game)
        return ["human"] + list_bot_types

    def _select_game(self, game: str, *args):
        """
        Callback function for the Dropselect menu used to select the game.

        Parameters:
            game (str): game selected in the drop-select menu
            *args: additional arguments passed by pygame_menu (unused)
        """
        self._selected_game = game[0][0]
        self._list_player_types = self._get_game_available_bots_with_human(
            self._selected_game
        )

        drop_select_items = [
            (player_type, i) for i, player_type in enumerate(self._list_player_types)
        ]
        self._menu_dropselect_player1.update_items(drop_select_items)
        self._menu_dropselect_player2.update_items(drop_select_items)

    def _select_player(self, player_num: int, player_type: str):
        """
        Callback function for the Dropselect menu used to select a player's Bot type.

        Parameters:
            player_num (int): player number (1 or 2)
            player_type (str): player type selected in the drop-select menu
        """
        selected_type = player_type[0][0]
        if player_num == 1:
            self._selected_player1_type = selected_type
        elif player_num == 2:
            self._selected_player2_type = selected_type

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

    def get_selected_player(self, player_num: int) -> str:
        """
        Getter which returns the current selected player's Bot type.

        Parameters:
            player_num (int): player number (1 or 2)

        Returns:
            selected_player_type (str): Player's type selected in the menu
        """
        if player_num == 1:
            return self._selected_player1_type
        elif player_num == 2:
            return self._selected_player2_type
        else:
            raise ValueError(f"Invalid player number: {player_num}. Must be 1 or 2.")

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
