"""
game_engine.py - Complete Chess Game Engine
Handles all chess rules: moves, captures, castling, en passant,
pawn promotion, check, checkmate, stalemate, and draw conditions.
"""

from config import INITIAL_BOARD, BOARD_SIZE
from utils import deep_copy_board, board_to_algebraic, is_white_piece, is_black_piece


class Move:
    """Represents a chess move with all metadata."""

    def __init__(self, from_sq, to_sq, piece, captured=None,
                 promotion=None, is_castling=False, castle_side=None,
                 is_en_passant=False, is_double_pawn=False):
        self.from_sq = from_sq  # (col, row)
        self.to_sq = to_sq      # (col, row)
        self.piece = piece
        self.captured = captured
        self.promotion = promotion
        self.is_castling = is_castling
        self.castle_side = castle_side  # 'K' or 'Q'
        self.is_en_passant = is_en_passant
        self.is_double_pawn = is_double_pawn

    def to_algebraic(self):
        """Convert move to algebraic notation."""
        piece_upper = self.piece.upper()
        from_str = board_to_algebraic(*self.from_sq)
        to_str = board_to_algebraic(*self.to_sq)

        if self.is_castling:
            return "O-O" if self.castle_side == 'K' else "O-O-O"

        notation = ""
        if piece_upper == 'P':
            if self.captured:
                notation = from_str[0] + "x" + to_str
            else:
                notation = to_str
            if self.promotion:
                notation += "=" + self.promotion.upper()
        else:
            notation = piece_upper
            if self.captured:
                notation += "x"
            notation += to_str

        return notation

    def __repr__(self):
        return f"Move({board_to_algebraic(*self.from_sq)}->{board_to_algebraic(*self.to_sq)})"


class GameEngine:
    """Complete chess game engine with full rule enforcement."""

    def _generate_960_board(self, seed=None):
        """Generate a valid Fischer Random Chess back rank, optionally with a seed."""
        import random
        rng = random.Random(seed)
        
        board = [['.' for _ in range(8)] for _ in range(8)]
        # Fill pawns
        for i in range(8):
            board[1][i] = 'p'
            board[6][i] = 'P'
            
        rank = ['.'] * 8
        
        # 1. Place Bishops on opposite colors
        dark_sq = rng.choice([0, 2, 4, 6])
        light_sq = rng.choice([1, 3, 5, 7])
        rank[dark_sq] = 'b'
        rank[light_sq] = 'b'
        
        # 2. Place Queen randomly in remaining 6 squares
        empty = [i for i, p in enumerate(rank) if p == '.']
        queen_pos = rng.choice(empty)
        rank[queen_pos] = 'q'
        
        # 3. Place Knights randomly in remaining 5 squares
        empty = [i for i, p in enumerate(rank) if p == '.']
        k1, k2 = rng.sample(empty, 2)
        rank[k1] = 'n'
        rank[k2] = 'n'
        
        # 4. Place Rooks and King in remaining 3 squares (Rook, King, Rook)
        empty = [i for i, p in enumerate(rank) if p == '.']
        rank[empty[0]] = 'r'
        rank[empty[1]] = 'k'
        rank[empty[2]] = 'r'
        
        self.rook_left_col = empty[0]
        self.king_start_col = empty[1]
        self.rook_right_col = empty[2]
        
        # Assign to board (White is uppercase)
        for i in range(8):
            board[0][i] = rank[i]
            board[7][i] = rank[i].upper()
            
        return board

    def __init__(self):
        self.reset()

    def reset(self, is_960=False, seed=None):
        """Reset the board to the initial position."""
        self.is_960 = is_960
        if is_960:
            self.board = self._generate_960_board(seed=seed)
        else:
            self.board = deep_copy_board(INITIAL_BOARD)
            self.king_start_col = 4
            self.rook_left_col = 0
            self.rook_right_col = 7

        self.white_turn = True
        self.move_history = []
        self.position_history = []  # for threefold repetition
        self.halfmove_clock = 0  # for 50-move rule
        self.fullmove_number = 1

        # Castling rights
        self.white_king_moved = False
        self.white_rook_a_moved = False
        self.white_rook_h_moved = False
        self.black_king_moved = False
        self.black_rook_a_moved = False
        self.black_rook_h_moved = False

        # En passant target square (col, row) or None
        self.en_passant_target = None

        # Game state
        self.is_check = False
        self.is_checkmate = False
        self.is_stalemate = False
        self.is_draw = False
        self.draw_reason = ""
        self.game_over = False
        self.winner = None  # 'white', 'black', or None (draw)

        # Captured pieces
        self.white_captured = []  # pieces captured by white (black pieces)
        self.black_captured = []  # pieces captured by black (white pieces)

        # Store initial position
        self.position_history.append(self._board_hash())

    def get_fen(self):
        """Get the current board state in FEN format."""
        fen = ""
        for r in range(BOARD_SIZE):
            empty = 0
            for c in range(BOARD_SIZE):
                piece = self.board[r][c]
                if piece == '.':
                    empty += 1
                else:
                    if empty > 0:
                        fen += str(empty)
                        empty = 0
                    fen += piece
            if empty > 0:
                fen += str(empty)
            if r < BOARD_SIZE - 1:
                fen += "/"
        
        # Side to move
        fen += " w" if self.white_turn else " b"
        return fen

    def load_fen(self, fen):
        """Initialize the board state from a FEN string."""
        self.reset()
        parts = fen.split(' ')
        board_part = parts[0]
        
        # Clear board
        self.board = [['.' for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        
        row = 0
        col = 0
        for char in board_part:
            if char == '/':
                row += 1
                col = 0
            elif char.isdigit():
                col += int(char)
            else:
                if row < BOARD_SIZE and col < BOARD_SIZE:
                    self.board[row][col] = char
                col += 1
                
        if len(parts) > 1:
            self.white_turn = (parts[1] == 'w')
            
        self.position_history = [self._board_hash()]
        self._update_game_state()

    def get_piece(self, col, row):
        """Get the piece at a board position."""
        if 0 <= col < BOARD_SIZE and 0 <= row < BOARD_SIZE:
            return self.board[row][col]
        return None

    def _set_piece(self, col, row, piece):
        """Set a piece at a board position."""
        self.board[row][col] = piece

    def _board_hash(self):
        """Create a hashable representation of the current position."""
        return (
            tuple(tuple(row) for row in self.board),
            self.white_turn,
            self.white_king_moved, self.white_rook_a_moved, self.white_rook_h_moved,
            self.black_king_moved, self.black_rook_a_moved, self.black_rook_h_moved,
            self.en_passant_target,
        )

    def _is_on_board(self, col, row):
        return 0 <= col < BOARD_SIZE and 0 <= row < BOARD_SIZE

    def _find_king(self, is_white):
        """Find the king's position."""
        king = 'K' if is_white else 'k'
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] == king:
                    return (c, r)
        return None

    def _is_square_attacked(self, col, row, by_white):
        """Check if a square is attacked by the given color."""
        # Check pawn attacks
        pawn = 'P' if by_white else 'p'
        pawn_dir = 1 if by_white else -1  # direction pawns attack FROM
        for dc in [-1, 1]:
            pr, pc = row + pawn_dir, col + dc
            if self._is_on_board(pc, pr) and self.board[pr][pc] == pawn:
                return True

        # Check knight attacks
        knight = 'N' if by_white else 'n'
        knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                        (1, -2), (1, 2), (2, -1), (2, 1)]
        for dc, dr in knight_moves:
            nc, nr = col + dc, row + dr
            if self._is_on_board(nc, nr) and self.board[nr][nc] == knight:
                return True

        # Check king attacks
        king = 'K' if by_white else 'k'
        for dc in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if dc == 0 and dr == 0:
                    continue
                nc, nr = col + dc, row + dr
                if self._is_on_board(nc, nr) and self.board[nr][nc] == king:
                    return True

        # Check sliding pieces (rook/queen straight, bishop/queen diagonal)
        # Rook/Queen - horizontal and vertical
        rook = 'R' if by_white else 'r'
        queen = 'Q' if by_white else 'q'
        for dc, dr in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nc, nr = col + dc, row + dr
            while self._is_on_board(nc, nr):
                piece = self.board[nr][nc]
                if piece != '.':
                    if piece == rook or piece == queen:
                        return True
                    break
                nc += dc
                nr += dr

        # Bishop/Queen - diagonal
        bishop = 'B' if by_white else 'b'
        for dc, dr in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nc, nr = col + dc, row + dr
            while self._is_on_board(nc, nr):
                piece = self.board[nr][nc]
                if piece != '.':
                    if piece == bishop or piece == queen:
                        return True
                    break
                nc += dc
                nr += dr

        return False

    def is_in_check(self, is_white):
        """Check if the given color's king is in check."""
        king_pos = self._find_king(is_white)
        if not king_pos:
            return False
        return self._is_square_attacked(king_pos[0], king_pos[1], not is_white)

    def _get_raw_moves(self, col, row):
        """Get all pseudo-legal moves for a piece (without check validation)."""
        piece = self.board[row][col]
        if piece == '.':
            return []

        is_white = piece.isupper()
        moves = []
        piece_upper = piece.upper()

        if piece_upper == 'P':
            moves = self._get_pawn_moves(col, row, is_white)
        elif piece_upper == 'N':
            moves = self._get_knight_moves(col, row, is_white)
        elif piece_upper == 'B':
            moves = self._get_bishop_moves(col, row, is_white)
        elif piece_upper == 'R':
            moves = self._get_rook_moves(col, row, is_white)
        elif piece_upper == 'Q':
            moves = self._get_queen_moves(col, row, is_white)
        elif piece_upper == 'K':
            moves = self._get_king_moves(col, row, is_white)

        return moves

    def _get_pawn_moves(self, col, row, is_white):
        """Get all pseudo-legal pawn moves."""
        moves = []
        direction = -1 if is_white else 1
        start_row = 6 if is_white else 1
        promo_row = 0 if is_white else 7
        piece = self.board[row][col]

        # Forward one
        nr = row + direction
        if self._is_on_board(col, nr) and self.board[nr][col] == '.':
            if nr == promo_row:
                for promo in (['Q', 'R', 'B', 'N'] if is_white else ['q', 'r', 'b', 'n']):
                    moves.append(Move((col, row), (col, nr), piece, promotion=promo))
            else:
                moves.append(Move((col, row), (col, nr), piece,
                                  is_double_pawn=(row == start_row and False)))
                # Forward two from start
                if row == start_row:
                    nr2 = row + 2 * direction
                    if self.board[nr2][col] == '.':
                        moves.append(Move((col, row), (col, nr2), piece, is_double_pawn=True))

        # Captures
        for dc in [-1, 1]:
            nc = col + dc
            nr = row + direction
            if not self._is_on_board(nc, nr):
                continue

            target = self.board[nr][nc]
            if target != '.' and (target.isupper() != is_white):
                if nr == promo_row:
                    for promo in (['Q', 'R', 'B', 'N'] if is_white else ['q', 'r', 'b', 'n']):
                        moves.append(Move((col, row), (nc, nr), piece,
                                          captured=target, promotion=promo))
                else:
                    moves.append(Move((col, row), (nc, nr), piece, captured=target))

            # En passant
            if self.en_passant_target and (nc, nr) == self.en_passant_target:
                captured_pawn = self.board[row][nc]
                moves.append(Move((col, row), (nc, nr), piece,
                                  captured=captured_pawn, is_en_passant=True))

        return moves

    def _get_knight_moves(self, col, row, is_white):
        moves = []
        piece = self.board[row][col]
        offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                   (1, -2), (1, 2), (2, -1), (2, 1)]
        for dc, dr in offsets:
            nc, nr = col + dc, row + dr
            if self._is_on_board(nc, nr):
                target = self.board[nr][nc]
                if target == '.' or (target.isupper() != is_white):
                    captured = target if target != '.' else None
                    moves.append(Move((col, row), (nc, nr), piece, captured=captured))
        return moves

    def _get_sliding_moves(self, col, row, is_white, directions):
        moves = []
        piece = self.board[row][col]
        for dc, dr in directions:
            nc, nr = col + dc, row + dr
            while self._is_on_board(nc, nr):
                target = self.board[nr][nc]
                if target == '.':
                    moves.append(Move((col, row), (nc, nr), piece))
                elif target.isupper() != is_white:
                    moves.append(Move((col, row), (nc, nr), piece, captured=target))
                    break
                else:
                    break
                nc += dc
                nr += dr
        return moves

    def _get_bishop_moves(self, col, row, is_white):
        return self._get_sliding_moves(col, row, is_white,
                                       [(-1, -1), (-1, 1), (1, -1), (1, 1)])

    def _get_rook_moves(self, col, row, is_white):
        return self._get_sliding_moves(col, row, is_white,
                                       [(0, -1), (0, 1), (-1, 0), (1, 0)])

    def _get_queen_moves(self, col, row, is_white):
        return self._get_sliding_moves(col, row, is_white,
                                       [(-1, -1), (-1, 1), (1, -1), (1, 1),
                                        (0, -1), (0, 1), (-1, 0), (1, 0)])

    def _get_king_moves(self, col, row, is_white):
        moves = []
        piece = self.board[row][col]
        for dc in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if dc == 0 and dr == 0:
                    continue
                nc, nr = col + dc, row + dr
                if self._is_on_board(nc, nr):
                    target = self.board[nr][nc]
                    if target == '.' or (target.isupper() != is_white):
                        captured = target if target != '.' else None
                        moves.append(Move((col, row), (nc, nr), piece, captured=captured))

        # Castling (Disabled in 960 for simplicity due to UI constraints)
        if not self.is_960 and is_white and not self.white_king_moved and not self.is_in_check(True):
            # Kingside
            if (not self.white_rook_h_moved and
                    self.board[7][5] == '.' and self.board[7][6] == '.' and
                    self.board[7][7] == 'R' and
                    not self._is_square_attacked(5, 7, False) and
                    not self._is_square_attacked(6, 7, False)):
                moves.append(Move((4, 7), (6, 7), 'K', is_castling=True, castle_side='K'))
            # Queenside
            if (not self.white_rook_a_moved and
                    self.board[7][1] == '.' and self.board[7][2] == '.' and
                    self.board[7][3] == '.' and self.board[7][0] == 'R' and
                    not self._is_square_attacked(3, 7, False) and
                    not self._is_square_attacked(2, 7, False)):
                moves.append(Move((4, 7), (2, 7), 'K', is_castling=True, castle_side='Q'))

        elif not self.is_960 and not is_white and not self.black_king_moved and not self.is_in_check(False):
            # Kingside
            if (not self.black_rook_h_moved and
                    self.board[0][5] == '.' and self.board[0][6] == '.' and
                    self.board[0][7] == 'r' and
                    not self._is_square_attacked(5, 0, True) and
                    not self._is_square_attacked(6, 0, True)):
                moves.append(Move((4, 0), (6, 0), 'k', is_castling=True, castle_side='K'))
            # Queenside
            if (not self.black_rook_a_moved and
                    self.board[0][1] == '.' and self.board[0][2] == '.' and
                    self.board[0][3] == '.' and self.board[0][0] == 'r' and
                    not self._is_square_attacked(3, 0, True) and
                    not self._is_square_attacked(2, 0, True)):
                moves.append(Move((4, 0), (2, 0), 'k', is_castling=True, castle_side='Q'))

        return moves

    def get_legal_moves(self, col, row):
        """Get all legal moves for a piece at (col, row), filtering out moves that leave king in check."""
        piece = self.board[row][col]
        if piece == '.':
            return []

        is_white = piece.isupper()
        if is_white != self.white_turn:
            return []

        return [move for move in self._get_raw_moves(col, row) if self._is_legal_move(move)]

    def _is_legal_move(self, move):
        """Check if a move is legal (doesn't leave own king in check) without deep copies."""
        fc, fr = move.from_sq
        tc, tr = move.to_sq
        piece = self.board[fr][fc]
        target = self.board[tr][tc]
        ep_target = self.en_passant_target
        
        # Pseudo-apply move
        self.board[tr][tc] = piece
        self.board[fr][fc] = '.'
        ep_captured_pawn = None
        if move.is_en_passant:
            ep_captured_pawn = self.board[fr][tc]
            self.board[fr][tc] = '.'
            
        in_check = self.is_in_check(piece.isupper())
        
        # Restore state
        if move.is_en_passant:
            self.board[fr][tc] = ep_captured_pawn
        self.board[fr][fc] = piece
        self.board[tr][tc] = target
        self.en_passant_target = ep_target
        
        return not in_check

    def _apply_move_to_board(self, move):
        """Apply a move to the board (no validation, no state update)."""
        fc, fr = move.from_sq
        tc, tr = move.to_sq

        # En passant capture
        if move.is_en_passant:
            self.board[fr][tc] = '.'  # remove captured pawn

        # Move piece
        piece = move.promotion if move.promotion else self.board[fr][fc]
        self.board[tr][tc] = piece
        self.board[fr][fc] = '.'

        # Castling - move rook
        if move.is_castling:
            if move.castle_side == 'K':
                # Kingside
                rook_row = fr
                rook = self.board[rook_row][7]
                self.board[rook_row][7] = '.'
                self.board[rook_row][5] = rook
            else:
                # Queenside
                rook_row = fr
                rook = self.board[rook_row][0]
                self.board[rook_row][0] = '.'
                self.board[rook_row][3] = rook

    def get_all_legal_moves(self, is_white):
        """Get all legal moves for one side efficiently."""
        all_moves = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                piece = self.board[r][c]
                if piece != '.' and (piece.isupper() == is_white):
                    all_moves.extend(self.get_legal_moves(c, r))
        return all_moves

    def make_move(self, move):
        """Execute a move and update all game state."""
        fc, fr = move.from_sq
        tc, tr = move.to_sq

        # Track captured pieces
        if move.captured:
            if move.piece.isupper():
                self.white_captured.append(move.captured)
            else:
                self.black_captured.append(move.captured)

        # Update halfmove clock
        if move.piece.upper() == 'P' or move.captured:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        # Update castling rights
        if move.piece == 'K':
            self.white_king_moved = True
        elif move.piece == 'k':
            self.black_king_moved = True
        elif move.piece == 'R':
            if fc == 0 and fr == 7:
                self.white_rook_a_moved = True
            elif fc == 7 and fr == 7:
                self.white_rook_h_moved = True
        elif move.piece == 'r':
            if fc == 0 and fr == 0:
                self.black_rook_a_moved = True
            elif fc == 7 and fr == 0:
                self.black_rook_h_moved = True

        # If a rook is captured, update castling rights
        if move.captured:
            if tc == 0 and tr == 7:
                self.white_rook_a_moved = True
            elif tc == 7 and tr == 7:
                self.white_rook_h_moved = True
            elif tc == 0 and tr == 0:
                self.black_rook_a_moved = True
            elif tc == 7 and tr == 0:
                self.black_rook_h_moved = True

        # Apply to board
        self._apply_move_to_board(move)

        # Update en passant target
        if move.is_double_pawn:
            ep_row = (fr + tr) // 2
            self.en_passant_target = (fc, ep_row)
        else:
            self.en_passant_target = None

        # Save move
        self.move_history.append(move)

        # Switch turns
        if not self.white_turn:
            self.fullmove_number += 1
        self.white_turn = not self.white_turn

        # Record position
        self.position_history.append(self._board_hash())

        # Check game state
        self._update_game_state()

    def _update_game_state(self):
        """Update check, checkmate, stalemate, and draw conditions."""
        self.is_check = self.is_in_check(self.white_turn)
        legal_moves = self.get_all_legal_moves(self.white_turn)

        if not legal_moves:
            if self.is_check:
                self.is_checkmate = True
                self.game_over = True
                self.winner = 'black' if self.white_turn else 'white'
            else:
                self.is_stalemate = True
                self.is_draw = True
                self.draw_reason = "Stalemate"
                self.game_over = True
        elif self._is_insufficient_material():
            self.is_draw = True
            self.draw_reason = "Insufficient material"
            self.game_over = True
        elif self.halfmove_clock >= 100:  # 50 moves = 100 half-moves
            self.is_draw = True
            self.draw_reason = "50-move rule"
            self.game_over = True
        elif self._is_threefold_repetition():
            self.is_draw = True
            self.draw_reason = "Threefold repetition"
            self.game_over = True

    def _is_insufficient_material(self):
        """Check for insufficient material to checkmate."""
        white_pieces = []
        black_pieces = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                p = self.board[r][c]
                if p == '.':
                    continue
                if p.isupper():
                    white_pieces.append(p)
                else:
                    black_pieces.append(p)

        # King vs King
        if len(white_pieces) == 1 and len(black_pieces) == 1:
            return True
        # King + Bishop vs King, King + Knight vs King
        if len(white_pieces) == 1 and len(black_pieces) == 2:
            other = [p for p in black_pieces if p != 'k'][0]
            if other in ('b', 'n'):
                return True
        if len(black_pieces) == 1 and len(white_pieces) == 2:
            other = [p for p in white_pieces if p != 'K'][0]
            if other in ('B', 'N'):
                return True
        # King + Bishop vs King + Bishop (same color bishops)
        if len(white_pieces) == 2 and len(black_pieces) == 2:
            w_other = [p for p in white_pieces if p != 'K']
            b_other = [p for p in black_pieces if p != 'k']
            if w_other == ['B'] and b_other == ['b']:
                # Check if bishops are on same color
                wb_pos = None
                bb_pos = None
                for r in range(BOARD_SIZE):
                    for c in range(BOARD_SIZE):
                        if self.board[r][c] == 'B':
                            wb_pos = (c, r)
                        elif self.board[r][c] == 'b':
                            bb_pos = (c, r)
                if wb_pos and bb_pos:
                    if (wb_pos[0] + wb_pos[1]) % 2 == (bb_pos[0] + bb_pos[1]) % 2:
                        return True
        return False

    def _is_threefold_repetition(self):
        """Check if current position has occurred three times."""
        current = self.position_history[-1]
        count = self.position_history.count(current)
        return count >= 3

    def undo_move(self):
        """Undo the last move. Returns the undone Move or None."""
        if not self.move_history:
            return None

        # Full state restore &#8212; it's safest to replay all moves
        moves = self.move_history[:-1]
        undone = self.move_history[-1]
        self.reset()

        for move in moves:
            self.make_move(move)

        return undone

    def get_move_list_display(self):
        """Get formatted move list for display."""
        moves = []
        for i, move in enumerate(self.move_history):
            notation = move.to_algebraic()
            # Add check/checkmate symbols
            if i == len(self.move_history) - 1:
                if self.is_checkmate:
                    notation += "#"
                elif self.is_check:
                    notation += "+"
            move_num = i // 2 + 1
            if i % 2 == 0:
                moves.append(f"{move_num}. {notation}")
            else:
                moves[-1] += f"  {notation}"
        return moves

    def resign(self):
        """Current player resigns."""
        self.game_over = True
        self.winner = 'black' if self.white_turn else 'white'

    def offer_draw_accepted(self):
        """Draw by agreement."""
        self.game_over = True
        self.is_draw = True
        self.draw_reason = "Agreement"

    def timeout(self, is_white_timeout):
        """Handle timeout."""
        self.game_over = True
        self.winner = 'black' if is_white_timeout else 'white'
