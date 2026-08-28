const chessBoard = document.getElementById("chess-board");
const turnDisplay = document.getElementById("turn");
const messageDisplay = document.getElementById("message");

let selectedSquare = null;
let currentTurn = "white";

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

let board = {
    // Black pieces
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

    // White pieces
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

    if (startPosition === endPosition) {
        selectedSquare = null;
        if (messageDisplay) messageDisplay.textContent = "Selection cancelled.";
        return;
    }

    sendMoveToBackend(startPosition, endPosition);
    selectedSquare = null;
}

function removeSelection() {
    const selectedSquares = document.querySelectorAll(".selected");
    selectedSquares.forEach(function(square) {
        square.classList.remove("selected");
    });
}

function sendMoveToBackend(start, end) {
    if (messageDisplay) messageDisplay.textContent = "Checking move...";

    fetch("/api/move", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            from: start,
            to: end,
            color: currentTurn
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateBoard(start, end);
            switchTurn();
            if (messageDisplay) messageDisplay.textContent = "Move successful.";
        } else {
            if (messageDisplay) messageDisplay.textContent = data.message || "Invalid move.";
        }
    })
    .catch(error => {
        console.error(error);
        if (messageDisplay) messageDisplay.textContent = "Could not connect to the Python backend.";
    });
}

function updateBoard(start, end) {
    const piece = board[start];
    board[end] = piece;
    delete board[start];
    createBoard();
}

function switchTurn() {
    currentTurn = currentTurn === "white" ? "black" : "white";
    if (turnDisplay) turnDisplay.textContent = `${capitalize(currentTurn)}'s turn`;
}

function capitalize(text) {
    return text.charAt(0).toUpperCase() + text.slice(1);
}

createBoard();