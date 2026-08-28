import os
import sys

# Tell Python where the project root is on Vercel
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, request, jsonify
from backend.game import Game

app = Flask(__name__)
game = Game()

@app.route("/api/move", methods=["POST"])
def move():
    data = request.json
    start = data.get("from")
    end = data.get("to")
    
    success = game.move_piece(start, end)
    
    return jsonify({
        "success": success
    })