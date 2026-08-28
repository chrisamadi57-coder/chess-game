"""
rules.py

This file contains the rules of chess.

The Board class is responsible for:
    - storing the pieces
    - knowing what is on each square

The Piece classes are responsible for:
    - identifying each type of piece

This file is responsible for:
    - checking whether moves are legal
    - checking for check and checkmate
    - castling
    - en passant
    - promotion
    - draw rules
"""

import copy

from .pieces import Pawn, Rook, Knight, Bishop, Queen, King


class ChessRules:
    """
    Handles the rules of a chess game.

    The class receives a Board object and uses it to inspect
    and change the position of the pieces.
    """

    def __init__(self, board):
        """
        Create the rules manager.

        Parameters:
            board: A Board object.
        """

        self.board = board

        # Castling rights tell us whether each king and rook
        # is still allowed to castle.
        self.castling_rights = {
            "white": {
                "king_side": True,
                "queen_side": True
            },
            "black": {
                "king_side": True,
                "queen_side": True
            }
        }

        # This stores the square that can be captured by en passant.
        #
        # Example:
        # If a white pawn moves from e2 to e4,
        # en_passant_target becomes e3 -> (5, 4)
        #
        # It is None when en passant is not available.
        self.en_passant_target = None

        # Counts how many half-moves have happened without:
        # - a pawn move
        # - a capture
        #
        # This is used for the 50-move and 75-move rules.
        self.halfmove_clock = 0

        # Store previous board positions.
        #
        # This is used to detect repetition.
        self.position_history = []

    # =========================================================
    # BASIC MOVE CHECKING
    # =========================================================

    def is_legal_move(
        self,
        start_row,
        start_col,
        end_row,
        end_col,
        color
    ):
        """
        Check whether a move is completely legal.

        A move is legal when:

        1. There is a piece on the starting square.
        2. The piece belongs to the current player.
        3. The destination does not contain a friendly piece.
        4. The piece can move in that way.
        5. The move does not leave the player's king in check.

        Returns:
            True if the move is legal.
            False otherwise.
        """

        # Make sure the starting position is on the board.
        if not self.is_on_board(start_row, start_col):
            return False

        # Make sure the destination is on the board.
        if not self.is_on_board(end_row, end_col):
            return False

        piece = self.board.board[start_row][start_col]

        # There must be a piece to move.
        if piece is None:
            return False

        # The piece must belong to the player whose turn it is.
        if piece.color != color:
            return False

        destination = self.board.board[end_row][end_col]

        # You cannot capture your own piece.
        if destination is not None:
            if destination.color == color:
                return False

        # Check whether the normal movement of the piece is valid.
        if not self.piece_can_move(
            start_row,
            start_col,
            end_row,
            end_col
        ):
            return False

        # Make a temporary copy of the position.
        #
        # We do this because we need to ask:
        #
        # "What happens to my king if I make this move?"
        #
        # We don't want to permanently change the real board
        # while checking.
        board_backup = copy.deepcopy(self.board.board)
        en_passant_backup = self.en_passant_target
        castling_backup = copy.deepcopy(self.castling_rights)

        # Perform the move temporarily.
        self._perform_move(
            start_row,
            start_col,
            end_row,
            end_col,
            update_special_rules=False
        )

        # Check whether our king is now under attack.
        king_is_in_check = self.is_in_check(color)

        # Restore everything.
        self.board.board = board_backup
        self.en_passant_target = en_passant_backup
        self.castling_rights = castling_backup

        # A legal move cannot leave your king in check.
        if king_is_in_check:
            return False

        return True

    def piece_can_move(
        self,
        start_row,
        start_col,
        end_row,
        end_col
    ):
        """
        Check whether the piece movement itself is valid.

        This method checks things like:

            Pawn -> forward/diagonal movement
            Rook -> horizontal/vertical
            Bishop -> diagonal
            Knight -> L-shape
            Queen -> rook + bishop
            King -> one square

        It does NOT check whether moving the piece leaves the king
        in check.

        Returns:
            True if the piece can move that way.
            False otherwise.
        """

        piece = self.board.board[start_row][start_col]

        if piece is None:
            return False

        # -----------------------------------------------------
        # PAWN
        # -----------------------------------------------------

        if isinstance(piece, Pawn):

            direction = -1 if piece.color == "white" else 1

            starting_row = 6 if piece.color == "white" else 1

            row_difference = end_row - start_row
            col_difference = end_col - start_col

            destination = self.board.board[end_row][end_col]

            # Move forward by one square.
            if col_difference == 0 and row_difference == direction:
                return destination is None

            # Move forward by two squares from starting position.
            if (
                col_difference == 0
                and row_difference == 2 * direction
                and start_row == starting_row
            ):
                middle_row = start_row + direction

                return (
                    self.board.board[middle_row][start_col] is None
                    and destination is None
                )

            # Normal diagonal capture.
            if abs(col_difference) == 1 and row_difference == direction:

                # Normal capture.
                if destination is not None:
                    return destination.color != piece.color

                # En passant capture.
                if (
                    destination is None
                    and self.en_passant_target == (end_row, end_col)
                ):
                    return True

            return False

        # -----------------------------------------------------
        # ROOK
        # -----------------------------------------------------

        if isinstance(piece, Rook):

            # A rook moves horizontally or vertically.
            if start_row != end_row and start_col != end_col:
                return False

            return self.path_is_clear(
                start_row,
                start_col,
                end_row,
                end_col
            )

        # -----------------------------------------------------
        # KNIGHT
        # -----------------------------------------------------

        if isinstance(piece, Knight):

            row_difference = abs(end_row - start_row)
            col_difference = abs(end_col - start_col)

            return (
                row_difference == 2 and col_difference == 1
            ) or (
                row_difference == 1 and col_difference == 2
            )

        # -----------------------------------------------------
        # BISHOP
        # -----------------------------------------------------

        if isinstance(piece, Bishop):

            row_difference = abs(end_row - start_row)
            col_difference = abs(end_col - start_col)

            # A bishop moves diagonally.
            if row_difference != col_difference:
                return False

            return self.path_is_clear(
                start_row,
                start_col,
                end_row,
                end_col
            )

        # -----------------------------------------------------
        # QUEEN
        # -----------------------------------------------------

        if isinstance(piece, Queen):

            row_difference = abs(end_row - start_row)
            col_difference = abs(end_col - start_col)

            # Queen can move horizontally.
            horizontal = start_row == end_row

            # Queen can move vertically.
            vertical = start_col == end_col

            # Queen can move diagonally.
            diagonal = row_difference == col_difference

            if not (horizontal or vertical or diagonal):
                return False

            return self.path_is_clear(
                start_row,
                start_col,
                end_row,
                end_col
            )

        # -----------------------------------------------------
        # KING
        # -----------------------------------------------------

        if isinstance(piece, King):

            row_difference = abs(end_row - start_row)
            col_difference = abs(end_col - start_col)

            # Normal king movement.
            if row_difference <= 1 and col_difference <= 1:
                return True

            # Castling moves the king two squares.
            if row_difference == 0 and col_difference == 2:
                return self.can_castle(
                    piece.color,
                    start_row,
                    start_col,
                    end_col
                )

            return False

        return False

    # =========================================================
    # PATH CHECKING
    # =========================================================

    def path_is_clear(
        self,
        start_row,
        start_col,
        end_row,
        end_col
    ):
        """
        Check whether there are pieces blocking the path.

        This is needed for:

            Rooks
            Bishops
            Queens

        Knights do not need this because knights can jump.
        """

        row_difference = end_row - start_row
        col_difference = end_col - start_col

        # Work out which direction the piece is moving.
        row_step = 0
        col_step = 0

        if row_difference > 0:
            row_step = 1
        elif row_difference < 0:
            row_step = -1

        if col_difference > 0:
            col_step = 1
        elif col_difference < 0:
            col_step = -1

        row = start_row + row_step
        col = start_col + col_step

        # Continue until we reach the destination.
        while row != end_row or col != end_col:

            if self.board.board[row][col] is not None:
                return False

            row += row_step
            col += col_step

        return True

    # =========================================================
    # CASTLING
    # =========================================================

    def can_castle(
        self,
        color,
        start_row,
        start_col,
        end_col
    ):
        """
        Check whether castling is legal.

        There are two types:

            King side:
                e1 -> g1

            Queen side:
                e1 -> c1

        For black:

            e8 -> g8
            e8 -> c8

        The king:

            - cannot have moved before
            - cannot currently be in check
            - cannot move through check
            - cannot finish in check

        The rook also cannot have moved.
        """

        # The king should start on the e-file.
        if start_col != 4:
            return False

        if color == "white":
            row = 7
        else:
            row = 0

        # Make sure the king is actually on its starting square.
        king = self.board.board[row][4]

        if not isinstance(king, King):
            return False

        if king.color != color:
            return False

        # -----------------------------------------------------
        # KING-SIDE CASTLING
        # -----------------------------------------------------

        if end_col == 6:

            if not self.castling_rights[color]["king_side"]:
                return False

            rook = self.board.board[row][7]

            if not isinstance(rook, Rook):
                return False

            if rook.color != color:
                return False

            # f1/f8 and g1/g8 must be empty.
            if (
                self.board.board[row][5] is not None
                or self.board.board[row][6] is not None
            ):
                return False

            # The king cannot currently be in check.
            if self.is_in_check(color):
                return False

            # The king cannot pass through an attacked square.
            if self.square_is_attacked(row, 5, self.opposite_color(color)):
                return False

            # The destination square cannot be attacked.
            if self.square_is_attacked(row, 6, self.opposite_color(color)):
                return False

            return True

        # -----------------------------------------------------
        # QUEEN-SIDE CASTLING
        # -----------------------------------------------------

        if end_col == 2:

            if not self.castling_rights[color]["queen_side"]:
                return False

            rook = self.board.board[row][0]

            if not isinstance(rook, Rook):
                return False

            if rook.color != color:
                return False

            # b1/b8, c1/c8 and d1/d8 must be empty.
            if (
                self.board.board[row][1] is not None
                or self.board.board[row][2] is not None
                or self.board.board[row][3] is not None
            ):
                return False

            # The king cannot currently be in check.
            if self.is_in_check(color):
                return False

            # d1/d8 must not be attacked.
            if self.square_is_attacked(row, 3, self.opposite_color(color)):
                return False

            # c1/c8 must not be attacked.
            if self.square_is_attacked(row, 2, self.opposite_color(color)):
                return False

            return True

        return False

    # =========================================================
    # CHECK
    # =========================================================

    def is_in_check(self, color):
        """
        Check whether a player's king is currently in check.

        Returns:
            True if the king is under attack.
            False otherwise.
        """

        king_position = self.find_king(color)

        # A king should always exist in a normal chess game.
        if king_position is None:
            return True

        king_row, king_col = king_position

        opponent = self.opposite_color(color)

        return self.square_is_attacked(
            king_row,
            king_col,
            opponent
        )

    def square_is_attacked(self, row, col, attacking_color):
        """
        Check whether a square is attacked by a particular color.

        This is slightly different from normal move checking.

        For example, when checking whether a king can move to a square,
        we only care whether an enemy piece attacks that square.

        Returns:
            True if the square is attacked.
            False otherwise.
        """

        for start_row in range(8):

            for start_col in range(8):

                piece = self.board.board[start_row][start_col]

                if piece is None:
                    continue

                if piece.color != attacking_color:
                    continue

                # -------------------------------------------------
                # PAWN
                # -------------------------------------------------

                if isinstance(piece, Pawn):

                    direction = (
                        -1
                        if piece.color == "white"
                        else 1
                    )

                    row_difference = row - start_row
                    col_difference = col - start_col

                    if (
                        row_difference == direction
                        and abs(col_difference) == 1
                    ):
                        return True

                # -------------------------------------------------
                # KNIGHT
                # -------------------------------------------------

                elif isinstance(piece, Knight):

                    row_difference = abs(row - start_row)
                    col_difference = abs(col - start_col)

                    if (
                        (row_difference == 2 and col_difference == 1)
                        or
                        (row_difference == 1 and col_difference == 2)
                    ):
                        return True

                # -------------------------------------------------
                # KING
                # -------------------------------------------------

                elif isinstance(piece, King):

                    row_difference = abs(row - start_row)
                    col_difference = abs(col - start_col)

                    if (
                        row_difference <= 1
                        and col_difference <= 1
                        and (
                            row_difference != 0
                            or col_difference != 0
                        )
                    ):
                        return True

                # -------------------------------------------------
                # ROOK
                # -------------------------------------------------

                elif isinstance(piece, Rook):

                    if (
                        start_row == row
                        or start_col == col
                    ):
                        if self.path_is_clear(
                            start_row,
                            start_col,
                            row,
                            col
                        ):
                            return True

                # -------------------------------------------------
                # BISHOP
                # -------------------------------------------------

                elif isinstance(piece, Bishop):

                    row_difference = abs(row - start_row)
                    col_difference = abs(col - start_col)

                    if row_difference == col_difference:

                        if self.path_is_clear(
                            start_row,
                            start_col,
                            row,
                            col
                        ):
                            return True

                # -------------------------------------------------
                # QUEEN
                # -------------------------------------------------

                elif isinstance(piece, Queen):

                    row_difference = abs(row - start_row)
                    col_difference = abs(col - start_col)

                    horizontal_or_vertical = (
                        start_row == row
                        or start_col == col
                    )

                    diagonal = (
                        row_difference == col_difference
                    )

                    if horizontal_or_vertical or diagonal:

                        if self.path_is_clear(
                            start_row,
                            start_col,
                            row,
                            col
                        ):
                            return True

        return False

    def find_king(self, color):
        """
        Find the position of a player's king.

        Returns:
            A tuple such as (7, 4)
            or None if the king cannot be found.
        """

        for row in range(8):

            for col in range(8):

                piece = self.board.board[row][col]

                if isinstance(piece, King):
                    if piece.color == color:
                        return row, col

        return None

    # =========================================================
    # LEGAL MOVES
    # =========================================================

    def get_legal_moves(self, color):
        """
        Get all legal moves for a player.

        Returns:
            A list of tuples:

            [
                ((start_row, start_col), (end_row, end_col)),
                ...
            ]
        """

        legal_moves = []

        for start_row in range(8):

            for start_col in range(8):

                piece = self.board.board[start_row][start_col]

                if piece is None:
                    continue

                if piece.color != color:
                    continue

                for end_row in range(8):

                    for end_col in range(8):

                        if self.is_legal_move(
                            start_row,
                            start_col,
                            end_row,
                            end_col,
                            color
                        ):
                            legal_moves.append(
                                (
                                    (start_row, start_col),
                                    (end_row, end_col)
                                )
                            )

        return legal_moves

    def has_legal_moves(self, color):
        """
        Check whether a player has at least one legal move.
        """

        moves = self.get_legal_moves(color)

        return len(moves) > 0

    # =========================================================
    # CHECKMATE AND STALEMATE
    # =========================================================

    def is_checkmate(self, color):
        """
        Check whether a player is checkmated.

        Checkmate means:

            1. The king is in check.
            2. There are no legal moves.
        """

        if not self.is_in_check(color):
            return False

        if self.has_legal_moves(color):
            return False

        return True

    def is_stalemate(self, color):
        """
        Check whether a player is in stalemate.

        Stalemate means:

            1. The king is NOT in check.
            2. There are no legal moves.
        """

        if self.is_in_check(color):
            return False

        if self.has_legal_moves(color):
            return False

        return True

    # =========================================================
    # ACTUALLY MAKING A MOVE
    # =========================================================

    def move_piece(
        self,
        start_row,
        start_col,
        end_row,
        end_col,
        color,
        promotion="Q"
    ):
        """
        Make a legal move.

        Parameters:
            start_row: Starting row.
            start_col: Starting column.
            end_row: Ending row.
            end_col: Ending column.
            color: Player making the move.
            promotion: Piece to promote to.

        Returns:
            True if the move succeeds.
            False if the move is illegal.
        """

        if not self.is_legal_move(
            start_row,
            start_col,
            end_row,
            end_col,
            color
        ):
            return False

        # Remember whether the move is a capture
        # before the piece is moved.
        destination = self.board.board[end_row][end_col]

        is_capture = destination is not None

        piece = self.board.board[start_row][start_col]

        # En passant is a capture even though the destination
        # square is empty.
        en_passant_capture = (
            isinstance(piece, Pawn)
            and start_col != end_col
            and destination is None
            and self.en_passant_target == (end_row, end_col)
        )

        if en_passant_capture:
            is_capture = True

        # Perform the actual move.
        self._perform_move(
            start_row,
            start_col,
            end_row,
            end_col,
            update_special_rules=True
        )

        # Update castling rights after every move.
        self.update_castling_rights(
            start_row,
            start_col,
            end_row,
            end_col
        )

        # Handle pawn promotion.
        moved_piece = self.board.board[end_row][end_col]

        if isinstance(moved_piece, Pawn):

            if moved_piece.color == "white" and end_row == 0:
                self.promote_pawn(
                    end_row,
                    end_col,
                    promotion
                )

            elif moved_piece.color == "black" and end_row == 7:
                self.promote_pawn(
                    end_row,
                    end_col,
                    promotion
                )

        # -----------------------------------------------------
        # HALF-MOVE CLOCK
        # -----------------------------------------------------

        if isinstance(piece, Pawn) or is_capture:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        return True

    def _perform_move(
        self,
        start_row,
        start_col,
        end_row,
        end_col,
        update_special_rules=True
    ):
        """
        Perform a move on the board.

        The underscore at the beginning of the method name
        means this is mainly an internal helper.

        This method handles:

            - normal moves
            - captures
            - castling
            - en passant
        """

        piece = self.board.board[start_row][start_col]

        # -----------------------------------------------------
        # EN PASSANT
        # -----------------------------------------------------

        if isinstance(piece, Pawn):

            if (
                start_col != end_col
                and self.board.board[end_row][end_col] is None
                and self.en_passant_target == (end_row, end_col)
            ):
                # The captured pawn is on the same row as the
                # destination square.
                captured_row = end_row

                if piece.color == "white":
                    captured_row = end_row + 1
                else:
                    captured_row = end_row - 1

                self.board.board[captured_row][end_col] = None

        # -----------------------------------------------------
        # CASTLING
        # -----------------------------------------------------

        if isinstance(piece, King):

            if abs(end_col - start_col) == 2:

                # King side castling.
                if end_col == 6:

                    rook = self.board.board[start_row][7]

                    self.board.board[start_row][5] = rook
                    self.board.board[start_row][7] = None

                # Queen side castling.
                elif end_col == 2:

                    rook = self.board.board[start_row][0]

                    self.board.board[start_row][3] = rook
                    self.board.board[start_row][0] = None

        # -----------------------------------------------------
        # NORMAL MOVE
        # -----------------------------------------------------

        self.board.board[end_row][end_col] = piece
        self.board.board[start_row][start_col] = None

        # -----------------------------------------------------
        # EN PASSANT TARGET
        # -----------------------------------------------------

        if update_special_rules:

            # By default, there is no en passant target.
            self.en_passant_target = None

            # A pawn moving two squares creates an
            # en passant target.
            if isinstance(piece, Pawn):

                if abs(end_row - start_row) == 2:

                    middle_row = (
                        start_row + end_row
                    ) // 2

                    self.en_passant_target = (
                        middle_row,
                        start_col
                    )

    # =========================================================
    # CASTLING RIGHTS
    # =========================================================

    def update_castling_rights(
        self,
        start_row,
        start_col,
        end_row,
        end_col
    ):
        """
        Update castling rights after a move.

        A player loses castling rights when:

            - their king moves
            - their rook moves
            - their rook is captured
        """

        # -----------------------------------------------------
        # KING MOVED
        # -----------------------------------------------------

        piece = self.board.board[end_row][end_col]

        if isinstance(piece, King):

            color = piece.color

            self.castling_rights[color]["king_side"] = False
            self.castling_rights[color]["queen_side"] = False

        # -----------------------------------------------------
        # ROOK MOVED
        # -----------------------------------------------------

        if isinstance(piece, Rook):

            color = piece.color

            # White king-side rook.
            if start_row == 7 and start_col == 7:
                if color == "white":
                    self.castling_rights["white"]["king_side"] = False

            # White queen-side rook.
            if start_row == 7 and start_col == 0:
                if color == "white":
                    self.castling_rights["white"]["queen_side"] = False

            # Black king-side rook.
            if start_row == 0 and start_col == 7:
                if color == "black":
                    self.castling_rights["black"]["king_side"] = False

            # Black queen-side rook.
            if start_row == 0 and start_col == 0:
                if color == "black":
                    self.castling_rights["black"]["queen_side"] = False

        # -----------------------------------------------------
        # ROOK CAPTURED
        # -----------------------------------------------------

        # We check the destination square after the move.
        #
        # The captured rook is gone, so we use the destination
        # square and the starting player to determine which rook
        # could have been captured.
        #
        # This section is handled by checking whether the rook
        # was originally sitting on a corner.

        # The easiest way to handle this is by looking at
        # whether a corner rook still exists.

        self.check_rook_rights()

    def check_rook_rights(self):
        """
        Remove castling rights when the original corner rook
        is no longer on its starting square.
        """

        # White queen-side rook.
        white_queen_rook = self.board.board[7][0]

        if not (
            isinstance(white_queen_rook, Rook)
            and white_queen_rook.color == "white"
        ):
            self.castling_rights["white"]["queen_side"] = False

        # White king-side rook.
        white_king_rook = self.board.board[7][7]

        if not (
            isinstance(white_king_rook, Rook)
            and white_king_rook.color == "white"
        ):
            self.castling_rights["white"]["king_side"] = False

        # Black queen-side rook.
        black_queen_rook = self.board.board[0][0]

        if not (
            isinstance(black_queen_rook, Rook)
            and black_queen_rook.color == "black"
        ):
            self.castling_rights["black"]["queen_side"] = False

        # Black king-side rook.
        black_king_rook = self.board.board[0][7]

        if not (
            isinstance(black_king_rook, Rook)
            and black_king_rook.color == "black"
        ):
            self.castling_rights["black"]["king_side"] = False

    # =========================================================
    # PROMOTION
    # =========================================================

    def promote_pawn(self, row, col, promotion="Q"):
        """
        Replace a pawn with another piece.

        Valid choices:

            Q = Queen
            R = Rook
            B = Bishop
            N = Knight

        If an invalid choice is given, we use a queen.
        """

        pawn = self.board.board[row][col]

        if not isinstance(pawn, Pawn):
            return

        color = pawn.color

        promotion = promotion.upper()

        if promotion == "Q":
            new_piece = Queen(color)

        elif promotion == "R":
            new_piece = Rook(color)

        elif promotion == "B":
            new_piece = Bishop(color)

        elif promotion == "N":
            new_piece = Knight(color)

        else:
            # Queen is the default promotion.
            new_piece = Queen(color)

        self.board.board[row][col] = new_piece

    # =========================================================
    # DRAW RULES
    # =========================================================

    def position_key(self, current_turn):
        """
        Create a simple representation of the current position.

        We use:

            board position
            current player's turn
            castling rights
            en passant target

        This allows us to compare positions later.
        """

        board_position = []

        for row in range(8):

            row_data = []

            for col in range(8):

                piece = self.board.board[row][col]

                if piece is None:
                    row_data.append(".")

                else:
                    row_data.append(piece.symbol)

            board_position.append(
                "".join(row_data)
            )

        white_castling = (
            self.castling_rights["white"]["king_side"],
            self.castling_rights["white"]["queen_side"]
        )

        black_castling = (
            self.castling_rights["black"]["king_side"],
            self.castling_rights["black"]["queen_side"]
        )

        return (
            tuple(board_position),
            current_turn,
            white_castling,
            black_castling,
            self.en_passant_target
        )

    def record_position(self, current_turn):
        """
        Save the current position to the position history.

        The Game class should call this after each completed move.
        """

        key = self.position_key(current_turn)

        self.position_history.append(key)

    def repetition_count(self, current_turn):
        """
        Count how many times the current position has occurred.
        """

        key = self.position_key(current_turn)

        count = 0

        for position in self.position_history:

            if position == key:
                count += 1

        return count

    def is_threefold_repetition(self, current_turn):
        """
        Check whether the same position has occurred three times.

        This is a draw that can be claimed.
        """

        return self.repetition_count(current_turn) >= 3

    def is_fivefold_repetition(self, current_turn):
        """
        Check whether the same position has occurred five times.

        This is an automatic draw.
        """

        return self.repetition_count(current_turn) >= 5

    def is_fifty_move_draw(self):
        """
        Check the 50-move rule.

        50 full moves = 100 half-moves.
        """

        return self.halfmove_clock >= 100

    def is_seventy_five_move_draw(self):
        """
        Check the 75-move rule.

        75 full moves = 150 half-moves.
        """

        return self.halfmove_clock >= 150

    # =========================================================
    # INSUFFICIENT MATERIAL
    # =========================================================

    def is_insufficient_material(self):
        """
        Check for basic insufficient-material positions.

        Examples:

            King vs King
            King + Bishop vs King
            King + Knight vs King

        These positions cannot produce a checkmate
        with the pieces that remain.
        """

        pieces = []

        for row in range(8):

            for col in range(8):

                piece = self.board.board[row][col]

                if piece is not None:
                    pieces.append(piece)

        # Remove both kings from the count.
        non_king_pieces = []

        for piece in pieces:

            if not isinstance(piece, King):
                non_king_pieces.append(piece)

        # King vs King.
        if len(non_king_pieces) == 0:
            return True

        # King + one bishop vs King.
        if len(non_king_pieces) == 1:

            if isinstance(
                non_king_pieces[0],
                Bishop
            ):
                return True

            if isinstance(
                non_king_pieces[0],
                Knight
            ):
                return True

        # King + two bishops on same-colored squares
        # is also insufficient.
        if len(non_king_pieces) == 2:

            if all(
                isinstance(piece, Bishop)
                for piece in non_king_pieces
            ):

                bishop_colors = []

                for row in range(8):

                    for col in range(8):

                        piece = self.board.board[row][col]

                        if isinstance(piece, Bishop):

                            square_color = (
                                row + col
                            ) % 2

                            bishop_colors.append(
                                square_color
                            )

                if (
                    len(bishop_colors) == 2
                    and bishop_colors[0] == bishop_colors[1]
                ):
                    return True

        return False

    # =========================================================
    # GAME STATUS
    # =========================================================

    def get_game_status(self, current_turn):
        """
        Determine the current status of the game.

        Possible results include:

            ongoing
            check
            checkmate
            stalemate
            threefold_repetition
            fivefold_repetition
            fifty_move_draw
            seventy_five_move_draw
            insufficient_material
        """

        # Fivefold repetition is automatic.
        if self.is_fivefold_repetition(current_turn):
            return "fivefold_repetition"

        # The 75-move rule is automatic.
        if self.is_seventy_five_move_draw():
            return "seventy_five_move_draw"

        # Basic insufficient material.
        if self.is_insufficient_material():
            return "insufficient_material"

        # Checkmate.
        if self.is_checkmate(current_turn):
            return "checkmate"

        # Stalemate.
        if self.is_stalemate(current_turn):
            return "stalemate"

        # Threefold repetition can be claimed.
        if self.is_threefold_repetition(current_turn):
            return "threefold_repetition"

        # 50-move draw can be claimed.
        if self.is_fifty_move_draw():
            return "fifty_move_draw"

        # The king is in check, but there is still a legal move.
        if self.is_in_check(current_turn):
            return "check"

        return "ongoing"

    # =========================================================
    # HELPER FUNCTIONS
    # =========================================================

    def opposite_color(self, color):
        """
        Return the opposite chess color.
        """

        if color == "white":
            return "black"

        return "white"

    def is_on_board(self, row, col):
        """
        Check whether a row and column are inside the board.
        """

        return (
            0 <= row < 8
            and 0 <= col < 8
        )