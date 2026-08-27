from .pieces import Pawn, Rook, Knight, Bishop, Queen, King

class Board:
    def __init__(self):
        self.board = self.create_board()
        self.setup_pieces()

    def create_board(self):
        board = []

        for row in range(8):
            board.append([])

            for column in range(8):
                board[row].append(None)

        return board

    def setup_pieces(self):
        # Black pieces
        self.board[0][0] = Rook("black")
        self.board[0][1] = Knight("black")
        self.board[0][2] = Bishop("black")
        self.board[0][3] = Queen("black")
        self.board[0][4] = King("black")
        self.board[0][5] = Bishop("black")
        self.board[0][6] = Knight("black")
        self.board[0][7] = Rook("black")

        # Black pawns
        for column in range(8):
            self.board[1][column] = Pawn("black")

        # White pieces
        self.board[7][0] = Rook("white")
        self.board[7][1] = Knight("white")
        self.board[7][2] = Bishop("white")
        self.board[7][3] = Queen("white")
        self.board[7][4] = King("white")
        self.board[7][5] = Bishop("white")
        self.board[7][6] = Knight("white")
        self.board[7][7] = Rook("white")

        # White pawns
        for column in range(8):
            self.board[6][column] = Pawn("white")

    def display(self):
        print()
        print("     a b c d e f g h")
        print("    -----------------")

        for row in range(8):
            print(f"{8-row} |", end=" ")

            for column in range(8):
                piece = self.board[row][column]

                if piece is None:
                    print(".", end= " ")
                else:
                    print(piece.symbol, end=" ")
            print(f"| {8-row}")

        print("     ---------------")
        print("    a b c d e f g h")

    def get_piece(self, row, column):
        return self.board[row][column]