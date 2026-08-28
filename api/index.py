import os
import sys

# Ensure Python can resolve backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, request, jsonify
from backend.game import Game

app = Flask(__name__)

FILES = "abcdefgh"
COL_MAP = {f: i for i, f in enumerate(FILES)}


def square_to_coords(square_str):
    """Converts algebraic square (e.g. 'e2') to 0-indexed row and col."""
    if not square_str or len(square_str) != 2:
        return None, None

    file = square_str[0].lower()
    rank = square_str[1]

    if file not in COL_MAP or not rank.isdigit():
        return None, None

    row = 8 - int(rank)
    col = COL_MAP[file]

    if not (0 <= row < 8):
        return None, None

    return row, col


def coords_to_square(row, col):
    """Converts 0-indexed row/col back to algebraic notation, e.g. (6, 4) -> 'e2'."""
    return f"{FILES[col]}{8 - row}"


def build_game_from_history(history):
    """
    Reconstruct a Game by replaying every move in `history` from a
    brand-new starting position.

    This is the core of making the endpoint stateless: nothing about
    the game lives in server memory between requests. The client
    sends the full move list every time and we rebuild the position
    from scratch. A Vercel cold start, a scale-out to a second
    instance, or two different visitors hitting the function no
    longer causes drift, because there is no shared, long-lived
    game object to drift.

    Returns:
        (game, error_message) - game is None if any move in the
        history is illegal or malformed, which means the client's
        history was tampered with or corrupted.
    """

    game = Game()

    for index, entry in enumerate(history):
        start_row, start_col = square_to_coords(entry.get("from"))
        end_row, end_col = square_to_coords(entry.get("to"))
        promotion = entry.get("promotion", "Q")

        if start_row is None or end_row is None:
            return None, f"Malformed history entry at index {index}"

        success = game.move_piece(
            start_row, start_col, end_row, end_col, promotion
        )

        if not success:
            return None, (
                f"History replay failed at move {index + 1} "
                f"({entry.get('from')} -> {entry.get('to')})"
            )

    return game, None


def serialize_board(board):
    """
    Convert the internal row/col grid into the same
    {square: {color, piece}} shape the frontend already understands.

    The client never re-derives this itself and never patches its
    own copy after a move - it just replaces its board with whatever
    this returns. That means castling (rook jumping squares), en
    passant (a pawn disappearing off to the side), and promotion
    (a pawn becoming a queen) all render correctly automatically,
    because we're describing the real post-move position instead of
    the client guessing at it.
    """

    squares = {}

    for row in range(8):
        for col in range(8):
            piece = board.board[row][col]

            if piece is None:
                continue

            squares[coords_to_square(row, col)] = {
                "color": piece.color,
                "piece": type(piece).__name__.lower(),
            }

    return squares


@app.route("/api/new-game", methods=["POST", "GET"])
def new_game():
    """Return a fresh starting position and an empty history."""

    game = Game()

    return jsonify({
        "board": serialize_board(game.board),
        "turn": game.current_turn,
        "status": game.get_status(),
        "history": [],
    })


@app.route("/api/move", methods=["POST"])
def move():
    data = request.get_json(silent=True) or {}

    history = data.get("history", [])
    start_str = data.get("from")
    end_str = data.get("to")
    promotion = data.get("promotion", "Q")

    if not isinstance(history, list):
        return jsonify({"success": False, "message": "Invalid history"}), 400

    # Rebuild the whole game from the client-supplied history.
    # No global game object, so no state to go stale between requests.
    game, error = build_game_from_history(history)

    if game is None:
        return jsonify({"success": False, "message": error}), 400

    start_row, start_col = square_to_coords(start_str)
    end_row, end_col = square_to_coords(end_str)

    if start_row is None or end_row is None:
        return jsonify({"success": False, "message": "Invalid coordinates"}), 400

    try:
        success = game.move_piece(
            start_row, start_col, end_row, end_col, promotion
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

    if not success:
        return jsonify({
            "success": False,
            "message": "Illegal move",
            "board": serialize_board(game.board),
            "turn": game.current_turn,
        })

    updated_history = history + [{
        "from": start_str,
        "to": end_str,
        "promotion": promotion,
    }]

    return jsonify({
        "success": True,
        "board": serialize_board(game.board),
        "turn": game.current_turn,
        "status": game.get_status(),
        "history": updated_history,
    })