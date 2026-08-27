from board import Board

class Game:
    """
    Controls a chess game.

    The board class stores the pieces.
    The Game class controls what happens during the game.
    """

    def __init__(self):
        """Start a new chess game."""

        #Create the board
        self.board = Board()

        # White always moves first.
        self.current_turn = "white"

    def switch_turn(self):
        """Change the turn from white to black or blavk to white."""

        if self.current_turn == "white":
            self.current_turn ="black"
        else:
            self.current_turn = "white"

    def move_pieces(self, start_row, start_col, end_row, end_col):
        """
        Try to move the piece.

        Returns:
        True if the move was successful
        False if the move was not successful.
        """

        #Get the piece from the starting square.
        piece = self.board.get_piece(start_row, start_col)

        #---------------------------------
        # Check 1: Is there a piece there?
        #---------------------------------

        if piece is None:
            print("There is no piece on that square.")
            return False


        #-----------------------------------
        # Check 2: Is it this player's turn?
        #-----------------------------------

        if piece.color != self.current_turn:
            print(f"It is {self.current_turn}'s turn.")
            return False

        #----------------------------------
        # Check 3: Is the destination okay?
        #----------------------------------


        destination = self.board.get_piece(end_row, end_col)

        # You cannot capture your own piece
        if destination is not None:
            if destination.color == piece.color:
                print("You cannot capture your own piece.")
                return False

        #----------------------------------------
        # Check 4: Can this piece move like that?
        #----------------------------------------

        valid_move = piece.is_valid_move(
            start_row,
            start_col,
            end_row,
            end_col,
            self.board.board
        )


        if not valid_move:
            print("That piece cannot move like that.")
            return False


        #--------------
        # Make the move
        #--------------

        # Put the piece on the new square.
        self.board.board[end_row][end-col] = piece

        # Remove the piece from the old square.
        self.board.board[start_row][start_col] = None

        # Change the turn
        self.switch_turn()

        return True