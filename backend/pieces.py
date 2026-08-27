class Piece:
    def __init__(self, color):
        self.color = color
        self.symbol = "?"

    def is_valid_move(self, start_row, start_col, end_row, end_col, board):
        return False


class Pawn(Piece):
    def __init__(self, color):
        super().__init__(color)

        if color == "white":
            self.symbol = "P"
        else:
            self.symbol = "p"

    def is_valid_move(self, start_row, start_col, end_row, end_col, board):
        if self.color == "white":
            directon = -1
            starting_row = 6
        else:
            directon = 1
            starting_row = 1

        row_difference = end_row - start_row
        col_difference = end_col - start_col

        if col_difference == 0 and row_difference == directon:
            return board[end_row][end_col] is None

        if (
            col_difference == 0 and row_difference == 2 * direction
            and start_row == starting_row
        ):
            middle_row = start_row + direction

            return (
                board[middle_row][start_col] is None
                and board[end_row][end_col] is None
            )

        if abs(col_difference) == 1 and row_difference == direction:
            destination = board[end_row][end_col]

            if destination is not None and destination.color != self.color:
                return True
        return False


class Rook(Piece):
    def __init__(self, color):
        super().__init__(color)

        if color == "white":
            self.symbol = "R"
        else:
            self.symbol = "r"

    def is_valid_move(self, start_row, start_col, end_row, end_col, board):
        if start_row != end_row and start_col != end_col:
            return False

        if start_row == end_row:
            step = 1 if end_col > start_col else -1

            for col in range(start_col + step, end_col, step):
                if board[start_row][col] is not None:
                    return False

        else:
            step = 1 if end_row > start_row else -1

            for row in range(start_row + step, end_row, step):
                if board[row][start_col] is not None:
                    return False

        return True


class Knight(Piece):
    def __init__(self, color):
        super().__init__(color)

        if color == "white":
            self.symbol = "N"
        else:
            self.symbol = "n"

    def is_valid_move(self, start_row, start_col, end_row, end_col, board):
        row_difference = abs(end_row - start_row)
        col_difference = abs(end_col - start_col)

        return (row_difference == 2 and col_difference ==  1) or (
            row_difference == 1 and col_difference == 2
        )


class Bishop(Piece):
    def __init__(self, color):
        super().__init__(color)

        if color == "white":
            self.symbol = "B"
        else:
            self.symbol = "b"

    def is_valid_move(self, start_row, start_col, end_row, end_col, board):
        row_difference = abs(end_row - start_row)
        col_difference = abs(end_col - start_col)

        if row_difference != col_difference:
            return False

        row_step = 1 if end_row > start_row else -1
        col_step = 1 if end_col > start_col else -1

        row = start_row + row_step
        col = start_col + col_step

        while row != end_row:
            if board[row][col] is not None:
                return False

            row += row_step
            col += col_step

        return True


class Queen(Piece):
    def __init__(self, color):
        super().__init__(color)

        if color == "white":
            self.symbol = "Q"
        else:
            self.symbol = "q"

    def is_valid_move(self, start_row, start_col, end_row, end_col, board):
        row_difference = abs(end_row - start_row)
        col_difference = abs(end_col - start_col)

        if start_row == end_row or start_col == end_col:
            if start_row == end_row:
                step = 1 if end_col > start_col else -1

                for col in range(start_col + step, end_col, step):
                    if board[start_row][col] is not None:
                        return False
            else:
                step = 1 if end_row > start_row else -1

                for row in range(start_row + step, end_row, step):
                    if board[row][start_col] is not None:
                        return False

            return True

        if row_difference == col_difference:
            row_step = 1 if end_row > start_row else -1
            col_step = 1 if end_col > start_col else -1

            row = start_row + row_step
            col = start_col + col_step

            while row != end_row:
                if board[row][col] is not None:
                    return False

                row += row_step
                col += col_step

            return True
        
        return False


class King(Piece):
    def __init__(self, color):
        super().__init__(color)

        if color == "white":
            self.symbol = "K"
        else:
            self.symbol = "k"

    def is_valid_move(self, start_row, start_col, end_row, end_col, board):
        row_difference = abs(end_row - start_row)
        col_difference = abs(end_col - start_col)

        return row_difference <= 1 and col_difference <= 1