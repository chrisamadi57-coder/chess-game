const chessBoard = document.getElementById("chess-board");
const turnDisplay = document.getElementById("turn");
const messageDisplay = document.getElementById("message");

let selectedSquare = null;
let currentTurn = "white";
let moveHistory = [];
let gameOver = false;

const pieces = {
    white: {
        king: "♔",
        queen: "♕",
        rook: "♖",
        bishop: "♗",
        knight: "♘",
        pawn: "♙"
    },
    black: {
        king: "♚",
        queen: "♛",
        rook: "♜",
        bishop: "♝",
        knight: "♞",
        pawn: "♟"
    }
};

// This starting layout is only ever used for the very first paint,
// before the server has had a chance to respond. From the moment
// the first /api/new-game or /api/move response comes back, `board`
// is fully replaced by whatever the server sends - it is never
// patched or guessed at locally. That's deliberate: the server is
// the single source of truth for game state, so the client can't
// drift out of sync with it (which is what caused the old bug).
let board = {
    a8: { color: "black", piece: "rook" },
    b8: { color: "black", piece: "knight" },
    c8: { color: "black", piece: "bishop" },
    d8: { color: "black", piece: "queen" },
    e8: { color: "black", piece: "king" },
    f8: { color: "black", piece: "bishop" },
    g8: { color: "black", piece: "knight" },
    h8: { color: "black", piece: "rook" },
    a7: { color: "black", piece: "pawn" },
    b7: { color: "black", piece: "pawn" },
    c7: { color: "black", piece: "pawn" },
    d7: { color: "black", piece: "pawn" },
    e7: { color: "black", piece: "pawn" },
    f7: { color: "black", piece: "pawn" },
    g7: { color: "black", piece: "pawn" },
    h7: { color: "black", piece: "pawn" },

    a2: { color: "white", piece: "pawn" },
    b2: { color: "white", piece: "pawn" },
    c2: { color: "white", piece: "pawn" },
    d2: { color: "white", piece: "pawn" },
    e2: { color: "white", piece: "pawn" },
    f2: { color: "white", piece: "pawn" },
    g2: { color: "white", piece: "pawn" },
    h2: { color: "white", piece: "pawn" },
    a1: { color: "white", piece: "rook" },
    b1: { color: "white", piece: "knight" },
    c1: { color: "white", piece: "bishop" },
    d1: { color: "white", piece: "queen" },
    e1: { color: "white", piece: "king" },
    f1: { color: "white", piece: "bishop" },
    g1: { color: "white", piece: "knight" },
    h1: { color: "white", piece: "rook" }
};

function createBoard() {
    if (!chessBoard) return;
    chessBoard.innerHTML = "";

    const files = ["a", "b", "c", "d", "e", "f", "g", "h"];

    for (let row = 0; row < 8; row++) {
        for (let column = 0; column < 8; column++) {
            const square = document.createElement("div");
            square.classList.add("square");

            if ((row + column) % 2 === 0) {
                square.classList.add("white");
            } else {
                square.classList.add("black");
            }

            const file = files[column];
            const rank = 8 - row;
            const position = file + rank;

            square.dataset.position = position;
            addPieceToSquare(square, position);
            square.addEventListener("click", handleSquareClick);
            chessBoard.appendChild(square);
        }
    }
}

function addPieceToSquare(square, position) {
    const pieceInformation = board[position];
    if (!pieceInformation) return;

    const color = pieceInformation.color;
    const pieceType = pieceInformation.piece;
    const symbol = pieces[color][pieceType];

    square.textContent = symbol;
}

function handleSquareClick(event) {
    if (gameOver) return;

    const square = event.currentTarget;
    const position = square.dataset.position;

    if (selectedSquare === null) {
        const selectedPiece = board[position];

        if (!selectedPiece) {
            if (messageDisplay) messageDisplay.textContent = "There is no piece on that square.";
            return;
        }

        if (selectedPiece.color !== currentTurn) {
            if (messageDisplay) messageDisplay.textContent = `It is ${currentTurn}'s turn.`;
            return;
        }

        selectedSquare = position;
        square.classList.add("selected");
        if (messageDisplay) messageDisplay.textContent = `Selected ${position}`;
        return;
    }

    const startPosition = selectedSquare;
    const endPosition = position;

    removeSelection();
    selectedSquare = null;

    if (startPosition === endPosition) {
        if (messageDisplay) messageDisplay.textContent = "Selection cancelled.";
        return;
    }

    const promotion = getPromotionChoice(startPosition, endPosition);

    sendMoveToBackend(startPosition, endPosition, promotion);
}

function getPromotionChoice(start, end) {
    // Only relevant for a pawn reaching the last rank. Defaults to
    // queen if the piece isn't a pawn, the move isn't to the last
    // rank, or the user cancels the prompt.
    const moving = board[start];
    const endRank = end[1];

    const reachingLastRank =
        moving &&
        moving.piece === "pawn" &&
        ((moving.color === "white" && endRank === "8") ||
            (moving.color === "black" && endRank === "1"));

    if (!reachingLastRank) return "Q";

    const choice = window.prompt(
        "Promote to (Q)ueen, (R)ook, (B)ishop, or K(N)ight?",
        "Q"
    );

    if (!choice) return "Q";

    const normalized = choice.trim().toUpperCase();

    if (["Q", "R", "B", "N"].includes(normalized)) {
        return normalized;
    }

    return "Q";
}

function removeSelection() {
    const selectedSquares = document.querySelectorAll(".selected");
    selectedSquares.forEach(function(square) {
        square.classList.remove("selected");
    });
}

function startNewGame() {
    fetch("/api/new-game")
        .then(response => response.json())
        .then(data => {
            applyServerState(data);
            if (messageDisplay) messageDisplay.textContent = "New game started.";
        })
        .catch(error => {
            // If the server can't be reached, fall back to the
            // hardcoded starting position above so the board still
            // renders something instead of staying blank.
            console.error(error);
            if (messageDisplay) {
                messageDisplay.textContent =
                    "Could not reach the server - showing the starting position offline.";
            }
            createBoard();
        });
}

function sendMoveToBackend(start, end, promotion) {
    if (messageDisplay) messageDisplay.textContent = "Checking move...";

    fetch("/api/move", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            from: start,
            to: end,
            promotion: promotion,
            history: moveHistory
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                applyServerState(data);
                announceStatus(data.status);
            } else {
                // A rejected move never touches local state, so
                // there's nothing to roll back - the board the user
                // sees is still exactly what the server last
                // confirmed.
                if (messageDisplay) messageDisplay.textContent = data.message || "Invalid move.";
            }
        })
        .catch(error => {
            console.error(error);
            if (messageDisplay) messageDisplay.textContent = "Could not connect to the server.";
        });
}

function applyServerState(data) {
    // The server's board is the only board. Replace, don't merge.
    board = data.board;
    currentTurn = data.turn;
    moveHistory = data.history || [];

    createBoard();

    if (turnDisplay) turnDisplay.textContent = `${capitalize(currentTurn)}'s turn`;
}

function announceStatus(status) {
    if (!messageDisplay) return;

    const gameOverStatuses = new Set([
        "checkmate",
        "stalemate",
        "fivefold_repetition",
        "seventy_five_move_draw",
        "insufficient_material"
    ]);

    gameOver = gameOverStatuses.has(status);

    const messages = {
        checkmate: `Checkmate! ${capitalize(currentTurn === "white" ? "black" : "white")} wins.`,
        stalemate: "Stalemate - it's a draw.",
        check: `${capitalize(currentTurn)} is in check.`,
        fivefold_repetition: "Draw by fivefold repetition.",
        seventy_five_move_draw: "Draw by the 75-move rule.",
        insufficient_material: "Draw - insufficient material.",
        threefold_repetition: "Threefold repetition reached - a draw can be claimed.",
        fifty_move_draw: "50-move rule reached - a draw can be claimed.",
        ongoing: "Move successful."
    };

    messageDisplay.textContent = messages[status] || "Move successful.";
}

function capitalize(text) {
    return text.charAt(0).toUpperCase() + text.slice(1);
}

startNewGame();