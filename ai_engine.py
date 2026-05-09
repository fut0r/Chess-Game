"""
ai_engine.py - Chess AI using Minimax with Alpha-Beta Pruning
Supports multiple difficulty levels with piece-square table evaluation.
"""

import random
import time
from config import AI_DIFFICULTIES, PIECE_VALUES, BOARD_SIZE
from utils import deep_copy_board


# ---------------------------------------------------------------------------
# Piece-Square Tables (from White's perspective, mirrored for Black)
# Values encourage good piece placement
# ---------------------------------------------------------------------------

PAWN_TABLE = [
    [0,   0,   0,   0,   0,   0,   0,   0],
    [50,  50,  50,  50,  50,  50,  50,  50],
    [10,  10,  20,  30,  30,  20,  10,  10],
    [5,   5,   10,  25,  25,  10,   5,   5],
    [0,   0,   0,   20,  20,   0,   0,   0],
    [5,  -5,  -10,  0,   0,  -10, -5,   5],
    [5,   10,  10, -20, -20,  10,  10,   5],
    [0,   0,   0,   0,   0,   0,   0,   0],
]

KNIGHT_TABLE = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20,   0,   0,   0,   0, -20, -40],
    [-30,   0,  10,  15,  15,  10,   0, -30],
    [-30,   5,  15,  20,  20,  15,   5, -30],
    [-30,   0,  15,  20,  20,  15,   0, -30],
    [-30,   5,  10,  15,  15,  10,   5, -30],
    [-40, -20,   0,   5,   5,   0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],
]

BISHOP_TABLE = [
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10,   0,   0,   0,   0,   0,   0, -10],
    [-10,   0,  10,  10,  10,  10,   0, -10],
    [-10,   5,   5,  10,  10,   5,   5, -10],
    [-10,   0,  10,  10,  10,  10,   0, -10],
    [-10,  10,  10,  10,  10,  10,  10, -10],
    [-10,   5,   0,   0,   0,   0,   5, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20],
]

ROOK_TABLE = [
    [0,   0,   0,   0,   0,   0,   0,   0],
    [5,  10,  10,  10,  10,  10,  10,   5],
    [-5,  0,   0,   0,   0,   0,   0,  -5],
    [-5,  0,   0,   0,   0,   0,   0,  -5],
    [-5,  0,   0,   0,   0,   0,   0,  -5],
    [-5,  0,   0,   0,   0,   0,   0,  -5],
    [-5,  0,   0,   0,   0,   0,   0,  -5],
    [0,   0,   0,   5,   5,   0,   0,   0],
]

QUEEN_TABLE = [
    [-20, -10, -10,  -5,  -5, -10, -10, -20],
    [-10,   0,   0,   0,   0,   0,   0, -10],
    [-10,   0,   5,   5,   5,   5,   0, -10],
    [ -5,   0,   5,   5,   5,   5,   0,  -5],
    [  0,   0,   5,   5,   5,   5,   0,  -5],
    [-10,   5,   5,   5,   5,   5,   0, -10],
    [-10,   0,   5,   0,   0,   0,   0, -10],
    [-20, -10, -10,  -5,  -5, -10, -10, -20],
]

KING_MIDDLEGAME_TABLE = [
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [ 20,  20,   0,   0,   0,   0,  20,  20],
    [ 20,  30,  10,   0,   0,  10,  30,  20],
]

KING_ENDGAME_TABLE = [
    [-50, -40, -30, -20, -20, -30, -40, -50],
    [-30, -20, -10,   0,   0, -10, -20, -30],
    [-30, -10,  20,  30,  30,  20, -10, -30],
    [-30, -10,  30,  40,  40,  30, -10, -30],
    [-30, -10,  30,  40,  40,  30, -10, -30],
    [-30, -10,  20,  30,  30,  20, -10, -30],
    [-30, -30,   0,   0,   0,   0, -30, -30],
    [-50, -30, -30, -30, -30, -30, -30, -50],
]

PIECE_SQUARE_TABLES = {
    'P': PAWN_TABLE,
    'N': KNIGHT_TABLE,
    'B': BISHOP_TABLE,
    'R': ROOK_TABLE,
    'Q': QUEEN_TABLE,
}


class AIEngine:
    """Chess AI with configurable difficulty using Minimax + Alpha-Beta pruning."""

    def __init__(self, difficulty="Medium"):
        self.set_difficulty(difficulty)
        self.nodes_evaluated = 0
        self.best_move = None

    def set_difficulty(self, difficulty):
        """Set AI difficulty level."""
        self.difficulty = difficulty
        settings = AI_DIFFICULTIES.get(difficulty, AI_DIFFICULTIES["Medium"])
        self.max_depth = settings["depth"]
        self.noise = settings["noise"]

    async def get_best_move(self, engine):
        """Get the best move for the current position (Async for Web)."""
        self.nodes_evaluated = 0
        self.best_move = None
        import asyncio
        start_time = time.time()

        legal_moves = engine.get_all_legal_moves(engine.white_turn)

        if not legal_moves:
            return None

        if len(legal_moves) == 1:
            return legal_moves[0]

        # Shuffle for variety
        random.shuffle(legal_moves)

        # Order moves for better pruning
        legal_moves = self._order_moves(legal_moves, engine)

        is_maximizing = engine.white_turn
        best_score = float('-inf') if is_maximizing else float('inf')
        best_move = legal_moves[0]

        alpha = float('-inf')
        beta = float('inf')

        for move in legal_moves:
            # Crucial for Web: give back control to browser between move evaluations
            await asyncio.sleep(0)
            
            # Save state
            saved = self._save_state(engine)

            engine.make_move(move)

            score = self._minimax(engine, self.max_depth - 1, alpha, beta,
                                  not is_maximizing)

            # Add noise for easier difficulties
            if self.noise > 0:
                score += random.uniform(-self.noise * 100, self.noise * 100)

            # Restore state
            self._restore_state(engine, saved)

            if is_maximizing:
                if score > best_score:
                    best_score = score
                    best_move = move
                alpha = max(alpha, score)
            else:
                if score < best_score:
                    best_score = score
                    best_move = move
                beta = min(beta, score)

        elapsed = time.time() - start_time
        return best_move

    def _minimax(self, engine, depth, alpha, beta, is_maximizing):
        """Minimax with Alpha-Beta pruning."""
        self.nodes_evaluated += 1

        if depth == 0 or engine.game_over:
            return self._evaluate(engine)

        legal_moves = engine.get_all_legal_moves(engine.white_turn)

        if not legal_moves:
            if engine.is_in_check(engine.white_turn):
                # Checkmate - return very bad score for side to move
                return -99999 if is_maximizing else 99999
            return 0  # Stalemate

        # Move ordering
        legal_moves = self._order_moves(legal_moves, engine)

        if is_maximizing:
            max_eval = float('-inf')
            for move in legal_moves:
                saved = self._save_state(engine)
                engine.make_move(move)
                eval_score = self._minimax(engine, depth - 1, alpha, beta, False)
                self._restore_state(engine, saved)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                saved = self._save_state(engine)
                engine.make_move(move)
                eval_score = self._minimax(engine, depth - 1, alpha, beta, True)
                self._restore_state(engine, saved)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def _evaluate(self, engine):
        """Evaluate the current board position."""
        if engine.is_checkmate:
            return -99999 if engine.white_turn else 99999
        if engine.is_draw:
            return 0

        score = 0
        total_material = 0
        white_bishops = 0
        black_bishops = 0

        # Count material for endgame detection
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                piece = engine.board[r][c]
                if piece != '.' and piece.upper() != 'K':
                    total_material += abs(PIECE_VALUES.get(piece, 0))

        is_endgame = total_material < 2600  # roughly when queens are off

        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                piece = engine.board[r][c]
                if piece == '.':
                    continue

                # Material value
                score += PIECE_VALUES.get(piece, 0)

                # Piece-square table bonus
                piece_upper = piece.upper()
                if piece.isupper():  # White
                    if piece_upper == 'K':
                        table = KING_ENDGAME_TABLE if is_endgame else KING_MIDDLEGAME_TABLE
                    else:
                        table = PIECE_SQUARE_TABLES.get(piece_upper)
                    if table:
                        score += table[r][c]
                    if piece_upper == 'B':
                        white_bishops += 1
                else:  # Black (mirror the table)
                    if piece_upper == 'K':
                        table = KING_ENDGAME_TABLE if is_endgame else KING_MIDDLEGAME_TABLE
                    else:
                        table = PIECE_SQUARE_TABLES.get(piece_upper)
                    if table:
                        score -= table[7 - r][c]
                    if piece_upper == 'B':
                        black_bishops += 1

        # Bishop pair bonus
        if white_bishops >= 2:
            score += 30
        if black_bishops >= 2:
            score -= 30

        # Center control bonus (pawns and knights on central squares)
        center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
        extended_center = [(2, 2), (2, 3), (2, 4), (2, 5),
                           (3, 2), (3, 5), (4, 2), (4, 5),
                           (5, 2), (5, 3), (5, 4), (5, 5)]
        for c, r in center_squares:
            piece = engine.board[r][c]
            if piece != '.':
                bonus = 15
                if piece.isupper():
                    score += bonus
                else:
                    score -= bonus
        for c, r in extended_center:
            piece = engine.board[r][c]
            if piece != '.':
                bonus = 5
                if piece.isupper():
                    score += bonus
                else:
                    score -= bonus

        # Mobility bonus
        if self.max_depth >= 2:
            white_mobility = len(engine.get_all_legal_moves(True))
            black_mobility = len(engine.get_all_legal_moves(False))
            score += (white_mobility - black_mobility) * 4

        return score

    def _order_moves(self, moves, engine):
        """Order moves to improve alpha-beta pruning efficiency."""
        scored_moves = []
        for move in moves:
            score = 0
            # Captures first (MVV-LVA: Most Valuable Victim - Least Valuable Attacker)
            if move.captured:
                victim_val = abs(PIECE_VALUES.get(move.captured, 0))
                attacker_val = abs(PIECE_VALUES.get(move.piece, 0))
                score += 10000 + victim_val * 10 - attacker_val
            # Promotions are very valuable
            if move.promotion:
                promo_val = abs(PIECE_VALUES.get(move.promotion, 0))
                score += 9000 + promo_val
            # Castling is generally good
            if move.is_castling:
                score += 500
            # Center pawn moves in opening
            if move.piece.upper() == 'P':
                tc, tr = move.to_sq
                if tc in (3, 4) and tr in (3, 4):
                    score += 100
            # Knight/Bishop development
            if move.piece.upper() in ('N', 'B'):
                fc, fr = move.from_sq
                # Moving from back rank is good in opening
                if (move.piece.isupper() and fr == 7) or (not move.piece.isupper() and fr == 0):
                    score += 80
            # Check-giving moves (light check with saved state)
            scored_moves.append((score, move))

        scored_moves.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored_moves]

    def _save_state(self, engine):
        """Save complete engine state for undo during search."""
        return {
            'board': deep_copy_board(engine.board),
            'white_turn': engine.white_turn,
            'move_history': engine.move_history[:],
            'position_history': engine.position_history[:],
            'halfmove_clock': engine.halfmove_clock,
            'fullmove_number': engine.fullmove_number,
            'white_king_moved': engine.white_king_moved,
            'white_rook_a_moved': engine.white_rook_a_moved,
            'white_rook_h_moved': engine.white_rook_h_moved,
            'black_king_moved': engine.black_king_moved,
            'black_rook_a_moved': engine.black_rook_a_moved,
            'black_rook_h_moved': engine.black_rook_h_moved,
            'en_passant_target': engine.en_passant_target,
            'is_check': engine.is_check,
            'is_checkmate': engine.is_checkmate,
            'is_stalemate': engine.is_stalemate,
            'is_draw': engine.is_draw,
            'draw_reason': engine.draw_reason,
            'game_over': engine.game_over,
            'winner': engine.winner,
            'white_captured': engine.white_captured[:],
            'black_captured': engine.black_captured[:],
        }

    def _restore_state(self, engine, saved):
        """Restore engine state from saved snapshot."""
        engine.board = saved['board']
        engine.white_turn = saved['white_turn']
        engine.move_history = saved['move_history']
        engine.position_history = saved['position_history']
        engine.halfmove_clock = saved['halfmove_clock']
        engine.fullmove_number = saved['fullmove_number']
        engine.white_king_moved = saved['white_king_moved']
        engine.white_rook_a_moved = saved['white_rook_a_moved']
        engine.white_rook_h_moved = saved['white_rook_h_moved']
        engine.black_king_moved = saved['black_king_moved']
        engine.black_rook_a_moved = saved['black_rook_a_moved']
        engine.black_rook_h_moved = saved['black_rook_h_moved']
        engine.en_passant_target = saved['en_passant_target']
        engine.is_check = saved['is_check']
        engine.is_checkmate = saved['is_checkmate']
        engine.is_stalemate = saved['is_stalemate']
        engine.is_draw = saved['is_draw']
        engine.draw_reason = saved['draw_reason']
        engine.game_over = saved['game_over']
        engine.winner = saved['winner']
        engine.white_captured = saved['white_captured']
        engine.black_captured = saved['black_captured']
