const game = new Chess();
let selectedSquare = null;
let playerColor = 'w';
let isOnline = false;

// Piece mapping to assets
const pieceIcons = {
    'p': 'assets/pieces/black_pawn.png',
    'r': 'assets/pieces/black_rook.png',
    'n': 'assets/pieces/black_knight.png',
    'b': 'assets/pieces/black_bishop.png',
    'q': 'assets/pieces/black_queen.png',
    'k': 'assets/pieces/black_king.png',
    'P': 'assets/pieces/white_pawn.png',
    'R': 'assets/pieces/white_rook.png',
    'N': 'assets/pieces/white_knight.png',
    'B': 'assets/pieces/white_bishop.png',
    'Q': 'assets/pieces/white_queen.png',
    'K': 'assets/pieces/white_king.png',
};

function initBoard() {
    const boardEl = document.getElementById('board');
    boardEl.innerHTML = '';
    
    for (let r = 0; r < 8; r++) {
        for (let c = 0; c < 8; c++) {
            const square = document.createElement('div');
            const isLight = (r + c) % 2 === 0;
            const coord = String.fromCharCode(97 + c) + (8 - r);
            
            square.className = `square ${isLight ? 'light' : 'dark'}`;
            square.id = `sq-${coord}`;
            square.onclick = () => onSquareClick(coord);
            
            boardEl.appendChild(square);
        }
    }
    updateBoard();
    loadLeaderboard();
}

function updateBoard() {
    const board = game.board();
    for (let r = 0; r < 8; r++) {
        for (let c = 0; c < 8; c++) {
            const coord = String.fromCharCode(97 + c) + (8 - r);
            const squareEl = document.getElementById(`sq-${coord}`);
            squareEl.innerHTML = '';
            
            const piece = board[r][c];
            if (piece) {
                const img = document.createElement('img');
                const pieceKey = piece.color === 'w' ? piece.type.toUpperCase() : piece.type;
                img.src = pieceIcons[pieceKey];
                img.className = 'piece';
                squareEl.appendChild(img);
            }
        }
    }
}

function onSquareClick(coord) {
    if (selectedSquare === coord) {
        selectedSquare = null;
        clearHighlights();
        return;
    }

    if (selectedSquare) {
        const move = game.move({
            from: selectedSquare,
            to: coord,
            promotion: 'q' // Default to queen for simplicity
        });

        if (move) {
            updateBoard();
            selectedSquare = null;
            clearHighlights();
            checkGameOver();
            // Trigger AI if in local mode
            if (!isOnline && !game.game_over()) {
                setTimeout(makeAIMove, 500);
            }
        } else {
            selectedSquare = coord;
            highlightSquare(coord);
        }
    } else {
        const piece = game.get(coord);
        if (piece && piece.color === (game.turn())) {
            selectedSquare = coord;
            highlightSquare(coord);
        }
    }
}

function highlightSquare(coord) {
    clearHighlights();
    document.getElementById(`sq-${coord}`).classList.add('highlight');
}

function clearHighlights() {
    document.querySelectorAll('.square').forEach(sq => sq.classList.remove('highlight'));
}

async function makeAIMove() {
    // Basic AI for now: Pick a random legal move
    const moves = game.moves();
    if (moves.length > 0) {
        const move = moves[Math.floor(Math.random() * moves.length)];
        game.move(move);
        updateBoard();
        checkGameOver();
    }
}

function checkGameOver() {
    if (game.game_over()) {
        let msg = "Game Over!";
        if (game.in_checkmate()) msg = "Checkmate!";
        else if (game.in_draw()) msg = "Draw!";
        document.getElementById('status-msg').innerText = msg;
    }
}

async function loadLeaderboard() {
    try {
        const res = await fetch('http://18.196.205.59:8000/leaderboard');
        const data = await res.json();
        const list = document.getElementById('leaderboard-list');
        list.innerHTML = '';
        
        data.forEach((user, index) => {
            const row = document.createElement('div');
            row.className = 'rank-row';
            let rankHtml = `<span class="rank-num">${index + 1}</span>`;
            if (index === 0) rankHtml = `<span class="rank-circle gold">1</span>`;
            if (index === 1) rankHtml = `<span class="rank-circle silver">2</span>`;
            if (index === 2) rankHtml = `<span class="rank-circle bronze">3</span>`;
            
            row.innerHTML = `
                ${rankHtml}
                <span class="rank-name">${user.username}</span>
                <span class="rank-elo">${user.elo}</span>
            `;
            list.appendChild(row);
        });
    } catch (e) {
        console.error("Leaderboard failed", e);
    }
}

window.onload = initBoard;
