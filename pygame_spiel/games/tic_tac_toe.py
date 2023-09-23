import typing as t
import pygame
import site
from pathlib import Path

from pygame_spiel.games import base


class TicTacToe(base.Game):
    def __init__(self, name, current_player):
        super().__init__(name, current_player)

        self._text_font = pygame.font.SysFont("Arial", 30)

        # TicTacToe vertical/horizontal lines
        self._line_h1_x_start, self._line_h1_y_start = 0, 200
        self._line_h1_x_end, self._line_h1_y_end = 600, 200
        self._line_h2_x_start, self._line_h2_y_start = 0, 400
        self._line_h2_x_end, self._line_h2_y_end = 600, 400
        self._line_v1_x_start, self._line_v1_y_start = 200, 0
        self._line_v1_x_end, self._line_v1_y_end = 200, 600
        self._line_v2_x_start, self._line_v2_y_start = 400, 0
        self._line_v2_x_end, self._line_v2_y_end = 400, 600

        package_path = site.getsitepackages()[0]

        self._x_image = pygame.image.load(
            Path(package_path) / "pygame_spiel/images/tic_tac_toe/x_image.png"
        ).convert_alpha()

        self._quadrant_pos_map_x = [
            (20, 20),
            (220, 20),
            (420, 20),
            (20, 220),
            (220, 220),
            (420, 220),
            (20, 420),
            (220, 420),
            (420, 420),
        ]
        self._quadrant_pos_map_circle = [
            (100, 100),
            (300, 100),
            (500, 100),
            (100, 300),
            (300, 300),
            (500, 300),
            (100, 500),
            (300, 500),
            (500, 500),
        ]

        self._list_x_pos, self._list_o_pos = [], []

    def _get_quadrant(self, x: int, y: int) -> int:
        """
        Returns the quadrant index given the x,y coordinates in the board.
        The quandrand indices are numbered 0 to 9 starting from top-left to
        bottom-right:
        0 1 2
        3 4 5
        6 7 8

        Examples:
            _get_quadrant(1, 1) -> 0
            _get_quadrant(220, 420) -> 7

        Parameters:
            x (int): x coordinate
            y (int): y coordinate

        Returns:
            index (int): quadrant index at the x,y coordinates
        """
        if y <= 200:
            if x <= 200:
                return 0
            elif x > 200 and x <= 400:
                return 1
            else:
                return 2
        elif y > 200 and y <= 400:
            if x <= 200:
                return 3
            elif x > 200 and x <= 400:
                return 4
            else:
                return 5
        else:
            if x <= 200:
                return 6
            elif x > 200 and x <= 400:
                return 7
            else:
                return 8

    def _draw_text(self, text: str, text_col: t.Tuple[int, int, int], x: int, y: int):
        """
        Draws a text on the board. Used to write whether the player has won or
        lost the game

        Parameters:
            text (str): text to visualize
            text_col (tuple): text's color in the format (red, blue, green)
            x (int): x coordinate
            y (int): y coordinate
        """
        img = self._text_font.render(text, True, text_col)
        self._screen.blit(img, (x, y))

    def play(self, mouse_pos, mouse_pressed):
        if self._current_player == 0 and (mouse_pressed[0]):
            action = self._get_quadrant(mouse_pos[0], mouse_pos[1])
            if self._quadrant_pos_map_x[action] not in self._list_x_pos:
                self._state.apply_action(action)
                self._bots[1].inform_action(self._state, self._current_player, action)
                if self._quadrant_pos_map_x[action] not in self._list_x_pos:
                    self._list_x_pos.append(self._quadrant_pos_map_x[action])
        elif self._current_player == 1:
            action = self._bots[1].step(self._state)
            if self._quadrant_pos_map_circle[action] not in self._list_o_pos:
                self._state.apply_action(action)
                if self._quadrant_pos_map_circle[action] not in self._list_o_pos:
                    self._list_o_pos.append(self._quadrant_pos_map_circle[action])

        self._current_player = self._state.current_player()

        # Visualization
        self._screen.fill("white")

        pygame.draw.line(
            self._screen,
            "black",
            (self._line_h1_x_start, self._line_h1_y_start),
            (self._line_h1_x_end, self._line_h1_y_end),
            2,
        )
        pygame.draw.line(
            self._screen,
            "black",
            (self._line_h2_x_start, self._line_h2_y_start),
            (self._line_h2_x_end, self._line_h2_y_end),
            2,
        )
        pygame.draw.line(
            self._screen,
            "black",
            (self._line_v1_x_start, self._line_v1_y_start),
            (self._line_v1_x_end, self._line_v1_y_end),
            2,
        )
        pygame.draw.line(
            self._screen,
            "black",
            (self._line_v2_x_start, self._line_v2_y_start),
            (self._line_v2_x_end, self._line_v2_y_end),
            2,
        )

        for x_pos in self._list_x_pos:
            self._screen.blit(self._x_image, x_pos)
        for o_pos in self._list_o_pos:
            pygame.draw.circle(self._screen, "black", o_pos, 60, width=4)

        if self._current_player == -4:
            rewards = self._state.rewards()
            if rewards[0] == 0 and rewards[1] == 0:
                self._draw_text(f"DRAW", (0, 0, 0), 220, 300)
            elif rewards[0] == 1:
                self._draw_text(f"Winner: player 0", (0, 0, 0), 220, 300)
            else:
                self._draw_text(f"Winner: player 1", (0, 0, 0), 220, 300)
