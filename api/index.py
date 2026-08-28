import os
import sys

# Ensure Python can resolve backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, request, jsonify
from backend.game import Game

app = Flask(__name__)
game = Game()

def square_to_coords(square_str):
    """Converts algebraic square (e.g. 'e2') to 0-indexed row and col."""
    if not square_str or len(square_str) != 2:
        return None, None
    
    col_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
    file = square_str[0].lower()
    rank = square_str[1]

    if file not in col_map or not rank.isdigit():
        return None, None

    col = col_map[file]
    row = 8 - int(rank)
    return row, col

@app.route("/api/move", methods=["POST"])
def move():
    data = request.get_json(silent=True) or {}
    start_str = data.get("from")
    end_str = data.get("to")

    start_row, start_col = square_to_coords(start_str)
    end_row, end_col = square_to_coords(end_str)

    if start_row is None or end_row is None:
        return jsonify({"success": False, "message": "Invalid coordinates"}), 400

    try:
        success = game.move_piece(start_row, start_col, end_row, end_col)
        return jsonify({"success": bool(success)})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500