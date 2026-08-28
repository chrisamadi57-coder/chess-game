from .board import Board
from .rules import ChessRules


class Game:
    """Controls the current chess game."""

    def __init__(self):
        """Start a new game."""

        self.board = Board()

        self.rules = ChessRules(self.board)

        self.current_turn = "white"

        # Store the first position.
        self.rules.record_position(self.current_turn)

    def switch_turn(self):
        """Change the current player."""

        if self.current_turn == "white":
            self.current_turn = "black"
        else:
            self.current_turn = "white"

    def move_piece(
        self,
        start_row,
        start_col,
        end_row,
        end_col,
        promotion="Q"
    ):
        """Try to make a move."""

        success = self.rules.move_piece(
            start_row,
            start_col,
            end_row,
            end_col,
            self.current_turn,
            promotion
        )

        if not success:
            return False

        # Change the player.
        self.switch_turn()

        # Save the new position for repetition checking.
        self.rules.record_position(
            self.current_turn
        )

        return True

    def get_status(self):
        """Return the current game status."""

        return self.rules.get_game_status(
            self.current_turn
        )