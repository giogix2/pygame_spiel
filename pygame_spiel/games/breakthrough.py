import pygame
import typing as t
import math
import site
from pathlib import Path

from pygame_spiel.games import base


class Breakthrough(base.Game):
    def __init__(self, name, current_player):
        super().__init__(name, current_player)

        self._player_color = "b" if self._current_player == 0 else "w"
        self._n_rows, self._n_cols, self._n_directions = 8, 8, 6
        package_path = site.getsitepackages()[0]

        # Load images
        self._background = pygame.image.load(
            Path(package_path) / "pygame_spiel/images/breakthrough/chess_board.png"
        ).convert_alpha()
        self._pawn_white = pygame.image.load(
            Path(package_path) / "pygame_spiel/images/breakthrough/pawn_white.png"
        ).convert_alpha()
        self._pawn_white_selected = pygame.image.load(
            Path(package_path)
            / "pygame_spiel/images/breakthrough/pawn_white_selected.png"
        ).convert_alpha()
        self._pawn_black = pygame.image.load(
            Path(package_path) / "pygame_spiel/images/breakthrough/pawn_black.png"
        ).convert_alpha()

        self._pawn_white = pygame.transform.scale(self._pawn_white, (95, 95))
        self._pawn_white_selected = pygame.transform.scale(
            self._pawn_white_selected, (95, 95)
        )
        self._pawn_black = pygame.transform.scale(self._pawn_black, (95, 95))

        self._selected_row, self._selected_col = None, None

    def _convert_mouse_position_to_grid(
        self, mouse_pos: t.Tuple[int, int]
    ) -> t.Tuple[int, int]:
        """
        Maps mouse x/y position to cell's row/column coordinates on the board.

        This function is used to retrieve the coordinates of the mouse position, which
        is used to determine whether the mouse's arrow is touching a selected token or
        empty cell.

        Parameters:
            mouse_pos (tuple): contains the x/y position of the mouse (0: X, 1: Y)

        Returns:
            row (int): cell's row
            col (int): cell's column
        """

        offset = 246
        cell_size = 84
        border_size = 6

        row = math.floor(
            (mouse_pos[1] - offset + border_size) / (cell_size + border_size)
        )
        col = math.floor(
            (mouse_pos[0] - offset + border_size) / (cell_size + border_size)
        )
        return row, col

    def _get_token_by_position(self, row: int, col: int) -> int:
        """
        Returns the token position given the tokens row and column.

        This function is used to simplify the mapping of the token position
        in the grid. Open_spiel uses an integer number to represent the position
        of a token in the grid, but it's sometimes simpler to represent the position
        as a row/column coordinate.

        Parameters:
            row (int): Token's row
            col (int): Token's column

        Returns:
            res (int): token's position id
        """

        return row * 10 + col + 1

    def _get_direction(
        self, selected_pawn_col: int, dest_col: int, player_color: str
    ) -> int:
        """
        Returns the direction of a selected token given a destination column.

        The output of this function is used to convert a token's move into an action id. This
        is because the implementation of breakthrough in open_spiel represents each possible
        action with a unique integer id.

        Parameters:
            selected_pawn_col (int): token's column
            dest_col (int): destination column of the token
            player_color (str): player's color

        Returns:
            dir (int): token's direction (value between 0 and 5)
        """

        directions = {"b": [0, 1, 2], "w": [3, 4, 5]}

        if selected_pawn_col - dest_col == 1:
            dir = directions[player_color][0]
        elif selected_pawn_col - dest_col == 0:
            dir = directions[player_color][1]
        elif selected_pawn_col - dest_col == -1:
            dir = directions[player_color][2]
        else:
            dir = 7  # Invalid direction
        return dir

    def _from_action_string_to_int(
        self,
        selected_pawn_row: int,
        selected_pawn_col: int,
        dest_row: int,
        dest_col: int,
        token: "str",
    ):
        """
        Retruns the action id given token's actual and destination position.

        Tihs function returns the numerical action id given a selected token's
        current and destination position. This is because the implementation of breakthrough
        in open_spiel represents each possible action with a unique integer id, which is uniquely
        linked to the token's current and destination position.

        To better understand the logic in this function, please refer to the following links in open_spiel
        which have been used as inspiration:
        * https://github.com/deepmind/open_spiel/blob/efa004d8c5f5088224e49fdc198c5d74b6b600d0/open_spiel/spiel_utils.cc#L50-L64
        * https://github.com/deepmind/open_spiel/blob/efa004d8c5f5088224e49fdc198c5d74b6b600d0/open_spiel/games/breakthrough.cc#L243

        Parameters:
            selected_pawn_row (int): current token's row
            selected_pawn_col (int): current token's column
            dest_row (int): destination token's row
            dest_col (int): destination token's column
            token (str): token in the destination cell (can be ".", "w" or "b")

        Returns:
            action (int): brekthrough's unique action id
        """

        if abs(selected_pawn_row - dest_row) > 1:
            # Pawns cannot jump for more than 1 step
            return None

        action_bases = [self._n_rows, self._n_rows, self._n_directions, 2]

        dir = self._get_direction(selected_pawn_col, dest_col, self._player_color)
        if dir == 7:
            # Pawns can only move in front or direct diagonal positions
            return None
        capture = 0 if token != "b" else 1
        digits = [selected_pawn_row, selected_pawn_col, dir, capture]

        action = 0
        one_plus_max = 1
        for i in range(len(action_bases) - 1, -1, -1):
            action += digits[i] * one_plus_max
            one_plus_max *= action_bases[i]

        return action

    def _get_coordinates_by_position(self, row: int, col: int) -> t.Tuple[int, int]:
        """
        Maps token's row/column coordinates to real coordinates in 2D plan (pygame screen).

        This function is used to retrieve the coordinates of a token on the screen,
        which are used to draw the token on the screen with PyGame.

        Parameters:
            row (int): Token's row
            col (int): Token's column

        Returns:
            x (int): token's X position on the screen
            y (int): token's Y position on the screen
        """

        offset = 240
        unit = 89
        x = col * unit + offset
        y = row * unit + offset
        return x, y

    def play(self, mouse_pos, mouse_pressed):
        if (
            (self._current_player == 0 and self._player_color == "b")
            or (self._current_player == 1 and self._player_color == "w")
        ) and (mouse_pressed[0]):
            row, col = self._convert_mouse_position_to_grid(mouse_pos)
            token = self._state_string[self._get_token_by_position(row, col)]
            if self._selected_row is None and token == self._player_color:
                self._selected_row, self._selected_col = row, col
            elif self._selected_row is not None and token == self._player_color:
                self._selected_row, self._selected_col = None, None
            elif self._selected_row is not None and token != self._player_color:
                # A paws has been selected. If no other pawn is chosen, do not change assignment.
                action = self._from_action_string_to_int(
                    self._selected_row, self._selected_col, row, col, token
                )
                if action is not None:
                    self._state.apply_action(action)
                    self._bots[1].inform_action(
                        self._state, self._current_player, action
                    )
                    self._selected_row, self._selected_col = None, None
        elif (self._current_player == 1 and self._player_color == "b") or (
            self._current_player == 0 and self._player_color == "w"
        ):
            action = self._bots[1].step(self._state)
            self._state.apply_action(action)

        self._current_player = self._state.current_player()
        self._state_string = self._state.to_string()

        # Visualization
        self._screen.blit(self._background, (0, 0))

        for row in range(8):
            for col in range(8):
                token = self._state_string[self._get_token_by_position(row, col)]
                x, y = self._get_coordinates_by_position(row, col)

                if token == "b":
                    # screen.blit(pawn_black, (x, y))
                    if row == self._selected_row and col == self._selected_col:
                        self._screen.blit(self._pawn_white_selected, (x, y))
                    else:
                        self._screen.blit(self._pawn_black, (x, y))
                elif token == "w":
                    if row == self._selected_row and col == self._selected_col:
                        self._screen.blit(self._pawn_white_selected, (x, y))
                    else:
                        self._screen.blit(self._pawn_white, (x, y))
