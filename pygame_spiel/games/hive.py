import pygame
import typing as t
import math
from pathlib import Path
import pyspiel
import re

from pygame_spiel.games import base


def parse_hive_board_string(board_string: str) -> list[list[str]]:
    """
    Parse the ANSI-colored Hive board string into a list of lists.

    Args:
        board_string: The string returned by ToString() when ansi_color_output_ is True

    Returns:
        List of lists where each inner list represents a row of the board.
        Each element is either a dash "-" or piece identifier (e.g., "wQ", "bA1").
        Empty spaces are removed from the internal lists.
    """

    # ANSI escape sequence patterns to remove
    ansi_patterns = [
        r"\033\[38;5;223m",  # white color
        r"\033\[1;31m",  # black color (red)
        r"\033\[1;39m",  # reset color
        r"\033\[[0-9;]*m",  # any other ANSI color codes
    ]

    # Remove all ANSI escape sequences
    cleaned_string = board_string
    for pattern in ansi_patterns:
        cleaned_string = re.sub(pattern, "", cleaned_string)

    # Split into lines and remove empty lines
    lines = [line for line in cleaned_string.split("\n") if line.strip()]

    # Parse each line into board content
    board_rows = []

    for line in lines:
        row_content = []
        i = 0

        while i < len(line):
            # Check for piece identifiers (e.g., "wQ", "bA1", "wG2*")
            piece_match = re.match(r"([wb][QABGSLMP]\d*)\*?", line[i:])

            if piece_match:
                # Found a piece
                piece = piece_match.group(1)
                row_content.append(piece)
                i += len(piece_match.group(0))  # Include asterisk if present
            elif line[i] == "-":
                # Found a dash (empty position)
                row_content.append("-")
                i += 1
            elif line[i] == " ":
                # Skip spaces (padding/indentation) - don't add to row_content
                i += 1
            else:
                # Skip any other characters
                i += 1

        # Only add non-empty rows
        if row_content:
            board_rows.append(row_content)

    return board_rows


def pad_board_grid(board_grid: list[list[str]], max_length: int) -> list[list[str]]:
    """
    Pad the inner lists with spaces to make them all the same length.

    Args:
        board_grid: List of lists representing the Hive board (output from parse_hive_board_string)
        max_length: The target length for all inner lists

    Returns:
        List of lists where all inner lists have the same length (max_length)
    """
    padded_grid = []

    for row in board_grid:
        current_length = len(row)
        if current_length < max_length:
            # Calculate how many spaces to add on each side
            spaces_to_add = max_length - current_length
            spaces_per_side = spaces_to_add // 2

            # Create padded row with equal spacing on both sides
            padded_row = [" "] * spaces_per_side + row + [" "] * spaces_per_side
            padded_grid.append(padded_row)
        else:
            # Row is already at max length, keep as is
            padded_grid.append(row)

    # For each row in padded_grid, add a white space in between each other element
    # First, find the maximum length after adding spaces
    max_final_length = max(len(row) * 2 - 1 for row in padded_grid)

    for idx, row in enumerate(padded_grid):
        new_row = []
        for i, elem in enumerate(row):
            new_row.append(elem)
            if i < len(row) - 1:
                new_row.append(" ")

        # Pad the new row to match the maximum final length
        current_final_length = len(new_row)
        if current_final_length < max_final_length:
            spaces_to_add = max_final_length - current_final_length
            spaces_per_side = spaces_to_add // 2
            new_row = [" "] * spaces_per_side + new_row + [" "] * spaces_per_side

        padded_grid[idx] = new_row

    return padded_grid


class Hive(base.Game):
    def __init__(self, name, current_player):
        super().__init__(name, current_player)
        self._game = pyspiel.load_game("hive(ansi_color_output=true)")
        self._state = self._game.new_initial_state()

        # Load images in a compact way
        package_dir = Path(__file__).parent.parent
        piece_names = [
            "ant",
            "queen",
            "grasshopper",
            "spider",
            "beetle",
            "ladybug",
            "pillbug",
            "mosquito",
        ]
        colors = ["white", "black"]

        images = {}
        for color in colors:
            for piece in piece_names:
                key = f"{color}_{piece}_image"
                path = package_dir / f"images/hive/{color}_{piece}.png"
                images[key] = pygame.image.load(path).convert_alpha()

        for key in images:
            images[key] = pygame.transform.smoothscale(images[key], (70, 70))

        # Compressed image unpacking and assignment
        piece_counts = {
            "ant": 3,
            "queen": 1,
            "grasshopper": 3,
            "spider": 2,
            "beetle": 2,
            "ladybug": 1,
            "pillbug": 1,
            "mosquito": 1,
        }
        for color in ["white", "black"]:
            for piece, count in piece_counts.items():
                img = images[f"{color}_{piece}_image"]
                for i in range(1, count + 1):
                    setattr(self, f"_{color}_{piece}{i}", img)

        self._action_start_index = 0
        self._last_clicked_action = None
        self._board_offset_x = 0
        self._board_offset_y = 0
        self._board_dragging = False
        self._board_drag_start = (0, 0)

    def play(
        self, mouse_pos: t.Tuple[int, int], mouse_pressed: t.Tuple[bool, bool, bool]
    ) -> None:

        # Check if game is over or current_player is invalid
        if (
            self._state.is_terminal()
            or self._current_player < 0
            or self._current_player >= len(self._bots)
        ):
            pass  # Game is over, just do visualization
        else:
            current_bot = self._bots[self._current_player]
            is_human_player = str(type(current_bot).__name__) == "HumanBot"

            list_action_strings = [
                self._state.action_to_string(action)
                for action in self._state.legal_actions()
            ]
            dict_action_string_to_int = {
                self._state.action_to_string(action): action
                for action in self._state.legal_actions()
            }

            if is_human_player and self._last_clicked_action:
                action = dict_action_string_to_int[self._last_clicked_action]
                self._state.apply_action(action)
                self._last_clicked_action = None
                print(self._state.to_string())
            elif not is_human_player:
                # Current player is a bot, let it make a move
                action = current_bot.step(self._state)
                if action in self._state.legal_actions():
                    self._execute_move(action)

            self._state_string = self._state.to_string()
            # Convert the state string into a list of lists (rows of characters)
            self._state_grid = parse_hive_board_string(self._state_string)
            self._current_player = self._state.current_player()

            max_length = len(
                self._state_grid[len(self._state_grid) // 2]
            )  # middle row has the widest width
            padded_grid = pad_board_grid(self._state_grid, max_length)

            # Clear the screen
            self._screen.fill((255, 255, 255))  # White background

            # Draw the board grid
            self.draw_board_grid(padded_grid, self._screen)

            # Draw the action strings at the bottom with start_index
            self.draw_action_strings(list_action_strings, self._screen)

            # Update the display
            pygame.display.flip()

    def _execute_move(self, action):
        """
        Execute a move and update the game state.

        Args:
            action (int): The action to apply to the game state.
        """
        self._state.apply_action(action)

        # Inform the other player about this move
        other_player = 1 - self._current_player
        self._bots[other_player].inform_action(
            self._state, self._current_player, action
        )

    def draw_board_grid(
        self,
        padded_grid: list[list[str]],
        screen: pygame.Surface,
        start_x: int = 50,
        start_y: int = 50,
    ):
        """
        Draw the padded grid on the Pygame screen with drag navigation.

        Args:
            padded_grid: 2D grid where each element is either " ", "-", or a piece identifier
            screen: Pygame surface to draw on
            start_x: Starting x position for the grid
            start_y: Starting y position for the grid
        """
        # Initialize board offset for drag navigation
        if not hasattr(self, "_board_offset_x"):
            self._board_offset_x = 0
        if not hasattr(self, "_board_offset_y"):
            self._board_offset_y = 0
        if not hasattr(self, "_board_dragging"):
            self._board_dragging = False
        if not hasattr(self, "_board_drag_start"):
            self._board_drag_start = (0, 0)

        # Handle mouse drag for board navigation
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]  # Left mouse button

        # Check if mouse is in the board area (excluding action strings area)
        board_area_rect = pygame.Rect(
            0, 0, screen.get_width(), screen.get_height() - 250
        )  # Leave space for action strings

        if board_area_rect.collidepoint(mouse_pos):
            if mouse_pressed and not self._board_dragging:
                # Start dragging
                self._board_dragging = True
                self._board_drag_start = mouse_pos
            elif not mouse_pressed and self._board_dragging:
                # Stop dragging
                self._board_dragging = False
            elif self._board_dragging and mouse_pressed:
                # Continue dragging - update offset
                dx = mouse_pos[0] - self._board_drag_start[0]
                dy = mouse_pos[1] - self._board_drag_start[1]
                self._board_offset_x += dx
                self._board_offset_y += dy
                self._board_drag_start = mouse_pos

        # Apply offset to starting positions
        adjusted_start_x = start_x + self._board_offset_x
        adjusted_start_y = start_y + self._board_offset_y

        # Get the actual dimensions of the hexagon image
        hex_width = self._white_ant1.get_width()
        hex_height = self._white_ant1.get_height()

        # Draw board background with offset
        board_bg_rect = pygame.Rect(
            adjusted_start_x - 20,
            adjusted_start_y - 20,
            len(padded_grid[0]) * hex_width * 0.51 + 40,
            len(padded_grid) * hex_height * 0.80 + 40,
        )
        pygame.draw.rect(
            screen, (245, 245, 245), board_bg_rect
        )  # Light gray background
        pygame.draw.rect(screen, (200, 200, 200), board_bg_rect, 2)  # Border

        for row_idx, row in enumerate(padded_grid):
            for col_idx, element in enumerate(row):
                # Use hex_width for horizontal spacing to prevent overlap
                x = adjusted_start_x + col_idx * (hex_width * 0.51)
                # Reduce vertical spacing by overlapping hexagons
                y = adjusted_start_y + row_idx * (hex_height * 0.80)

                if element == "-":
                    # Draw the ant image for dash symbols (already scaled in constructor)
                    # screen.blit(self._white_ant1, (x, y))
                    continue
                elif element == " ":
                    # Don't draw anything for empty spaces
                    continue
                is_white = element.startswith("w")
                piece_type = element[
                    1
                ]  # 2nd letter indicates piece type (e.g., wA -> white Ant)
                if piece_type == "A":
                    if is_white:
                        screen.blit(self._white_ant1, (x, y))
                    else:
                        screen.blit(self._black_ant1, (x, y))
                elif piece_type == "B":
                    if is_white:
                        screen.blit(self._white_beetle1, (x, y))
                    else:
                        screen.blit(self._black_beetle1, (x, y))
                elif piece_type == "G":
                    if is_white:
                        screen.blit(self._white_grasshopper1, (x, y))
                    else:
                        screen.blit(self._black_grasshopper1, (x, y))
                elif piece_type == "S":
                    if is_white:
                        screen.blit(self._white_spider1, (x, y))
                    else:
                        screen.blit(self._black_spider1, (x, y))
                elif piece_type == "Q":
                    if is_white:
                        screen.blit(self._white_queen1, (x, y))
                    else:
                        screen.blit(self._black_queen1, (x, y))
                elif piece_type == "M":
                    if is_white:
                        screen.blit(self._white_mosquito1, (x, y))
                    else:
                        screen.blit(self._black_mosquito1, (x, y))
                elif piece_type == "P":
                    if is_white:
                        screen.blit(self._white_pillbug1, (x, y))
                    else:
                        screen.blit(self._black_pillbug1, (x, y))
                elif piece_type == "L":
                    if is_white:
                        screen.blit(self._white_ladybug1, (x, y))
                    else:
                        screen.blit(self._black_ladybug1, (x, y))
                else:
                    raise ValueError(
                        f"Unknown piece type: {piece_type} at ({row_idx}, {col_idx}) with element '{element}'"
                    )

        # Draw navigation instructions when dragging
        if self._board_dragging:
            instruction_font = pygame.font.Font(None, 20)
            instruction_text = instruction_font.render(
                "Drag to move board", True, (100, 100, 100)
            )
            screen.blit(instruction_text, (10, 10))

    def draw_action_strings(
        self,
        action_strings: list[str],
        screen: pygame.Surface,
        width: int = None,
        height: int = 200,
        start_x: int = 50,
        start_y: int = None,
    ):
        """
        Draw the list of action strings in a contained window at the bottom of the screen.

        Args:
            action_strings: List of action strings to display
            screen: Pygame surface to draw on
            width: Width of the action strings window (defaults to screen width - 100)
            height: Height of the action strings window (default 200)
            start_x: Starting x position for the window (default 50)
            start_y: Starting y position for the window (defaults to screen height - height - 50)
        """
        # Set default width to be a bit smaller than the hive window
        if width is None:
            width = screen.get_width() - 100

        # Set default y position to be at the bottom of the screen
        if start_y is None:
            start_y = screen.get_height() - height - 50

        # Colors
        BACKGROUND_COLOR = (240, 240, 240)  # Light gray background
        BORDER_COLOR = (100, 100, 100)  # Dark gray border
        TEXT_COLOR = (50, 50, 50)  # Dark text
        TITLE_COLOR = (30, 30, 30)  # Darker text for title
        BUTTON_COLOR = (180, 180, 180)  # Light gray for buttons
        BUTTON_HOVER_COLOR = (160, 160, 160)  # Darker gray for button hover
        BUTTON_TEXT_COLOR = (50, 50, 50)  # Dark text for buttons
        STRING_HOVER_COLOR = (200, 220, 255)  # Light blue for string hover
        STRING_HOVER_BORDER = (100, 150, 200)  # Border color for hovered strings

        # Draw the background rectangle
        pygame.draw.rect(screen, BACKGROUND_COLOR, (start_x, start_y, width, height))
        pygame.draw.rect(screen, BORDER_COLOR, (start_x, start_y, width, height), 2)

        # Initialize font
        try:
            font = pygame.font.Font(None, 24)
            small_font = pygame.font.Font(None, 18)
        except:
            font = pygame.font.SysFont("arial", 24)
            small_font = pygame.font.SysFont("arial", 18)

        # Draw title
        title_text = font.render(
            "Available Actions (click to select):", True, TITLE_COLOR
        )
        screen.blit(title_text, (start_x + 10, start_y + 10))

        # Calculate text area
        text_area_y = start_y + 40
        text_area_height = height - 80  # Leave space for buttons
        line_height = 25
        button_height = 30
        button_width = 60

        # Calculate multi-column layout
        visible_lines = text_area_height // line_height
        total_lines = len(action_strings)
        text_width = width - 20
        column_padding = 10  # Space between columns

        # Calculate optimal number of columns and column width
        estimated_char_width = 8
        min_column_width = 100  # Minimum width for a column

        # Calculate how many columns can fit
        max_columns = max(
            1, (text_width + column_padding) // (min_column_width + column_padding)
        )

        # Calculate actual column width based on available space
        column_width = (text_width - (max_columns - 1) * column_padding) // max_columns

        # Calculate how many items can be displayed in total
        items_per_column = visible_lines
        total_items_per_page = max_columns * items_per_column

        # Update pagination for multi-column layout
        max_start_index = max(0, total_lines - total_items_per_page)
        self._action_start_index = max(
            0, min(self._action_start_index, max_start_index)
        )

        # Initialize click debouncing if not exists
        if not hasattr(self, "_last_clicked_action_frame"):
            self._last_clicked_action_frame = None
        if not hasattr(self, "_mouse_was_pressed"):
            self._mouse_was_pressed = False

        # Handle mouse events for button clicks
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = pygame.mouse.get_pressed()[0]  # Left mouse button

        # Draw up and down buttons
        up_button_rect = pygame.Rect(
            start_x + 10, start_y + height - 60, button_width, button_height
        )
        down_button_rect = pygame.Rect(
            start_x + 80, start_y + height - 60, button_width, button_height
        )

        # Check if mouse is hovering over buttons
        up_hover = up_button_rect.collidepoint(mouse_pos)
        down_hover = down_button_rect.collidepoint(mouse_pos)

        # Handle button clicks
        if mouse_clicked:
            if up_hover:
                # Move up by one column worth of items
                self._action_start_index = max(
                    0, self._action_start_index - items_per_column
                )
            elif down_hover:
                # Move down by one column worth of items
                self._action_start_index = min(
                    self._action_start_index + items_per_column, max_start_index
                )

        # Draw up button
        up_color = BUTTON_HOVER_COLOR if up_hover else BUTTON_COLOR
        pygame.draw.rect(screen, up_color, up_button_rect)
        pygame.draw.rect(screen, BORDER_COLOR, up_button_rect, 2)
        up_text = small_font.render("▲ Up", True, BUTTON_TEXT_COLOR)
        up_text_rect = up_text.get_rect(center=up_button_rect.center)
        screen.blit(up_text, up_text_rect)

        # Draw down button
        down_color = BUTTON_HOVER_COLOR if down_hover else BUTTON_COLOR
        pygame.draw.rect(screen, down_color, down_button_rect)
        pygame.draw.rect(screen, BORDER_COLOR, down_button_rect, 2)
        down_text = small_font.render("▼ Down", True, BUTTON_TEXT_COLOR)
        down_text_rect = down_text.get_rect(center=down_button_rect.center)
        screen.blit(down_text, down_text_rect)

        # Display action strings in multiple columns
        items_displayed = 0
        clicked_action = None

        for col in range(max_columns):
            col_x = start_x + 10 + col * (column_width + column_padding)

            for row in range(items_per_column):
                item_index = self._action_start_index + col * items_per_column + row

                if item_index >= len(action_strings):
                    break

                action_string = action_strings[item_index]

                # Truncate long strings to fit in the column
                max_chars = column_width // estimated_char_width
                if len(action_string) > max_chars:
                    action_string = action_string[: max_chars - 3] + "..."

                # Create clickable rectangle for this action string
                text_surface = small_font.render(action_string, True, TEXT_COLOR)
                text_rect = text_surface.get_rect()
                text_rect.x = col_x
                text_rect.y = text_area_y + (row * line_height)

                # Check if mouse is hovering over this action string
                is_hovering = text_rect.collidepoint(mouse_pos)

                # Handle click on action string with debouncing
                if mouse_clicked and is_hovering and not self._mouse_was_pressed:
                    clicked_action = action_string
                    print(f"Clicked action: {action_string}")

                # Draw background highlight if hovering
                if is_hovering:
                    highlight_rect = pygame.Rect(
                        col_x - 2,
                        text_rect.y - 2,
                        text_rect.width + 4,
                        text_rect.height + 4,
                    )
                    pygame.draw.rect(
                        screen, STRING_HOVER_COLOR, highlight_rect
                    )  # Light blue highlight
                    pygame.draw.rect(
                        screen, STRING_HOVER_BORDER, highlight_rect, 1
                    )  # Border

                # Draw the text
                screen.blit(text_surface, (col_x, text_rect.y))
                items_displayed += 1

                if items_displayed >= total_items_per_page:
                    break

            if items_displayed >= total_items_per_page:
                break

        # Store clicked action for potential use elsewhere
        if clicked_action:
            self._last_clicked_action = clicked_action

        # Update mouse state for debouncing
        self._mouse_was_pressed = mouse_clicked

        # Show navigation indicator
        if total_lines > total_items_per_page:
            current_page = (self._action_start_index // total_items_per_page) + 1
            total_pages = (
                total_lines + total_items_per_page - 1
            ) // total_items_per_page
            indicator_text = small_font.render(
                f"Page {current_page} of {total_pages} ({self._action_start_index + 1}-{min(self._action_start_index + total_items_per_page, total_lines)} of {total_lines} actions)",
                True,
                TEXT_COLOR,
            )
            screen.blit(indicator_text, (start_x + 150, start_y + height - 35))
