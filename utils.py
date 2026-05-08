"""
utils.py - Shared utility functions for the Chess Game
Coordinate conversions, notation helpers, and common operations.
Layout values are read dynamically from config module so they update
when resolution changes.
"""

import config as cfg
from config import BOARD_SIZE, FILES, RANKS


def pixel_to_board(px, py, flipped=False):
    """Convert pixel coordinates to board coordinates (col, row)."""
    col = (px - cfg.BOARD_OFFSET_X) // cfg.SQUARE_SIZE
    row = (py - cfg.BOARD_OFFSET_Y) // cfg.SQUARE_SIZE
    
    if flipped:
        col = 7 - col
        row = 7 - row
        
    if 0 <= col < BOARD_SIZE and 0 <= row < BOARD_SIZE:
        return (col, row)
    return None


def board_to_pixel(col, row, flipped=False):
    """Convert board coordinates to pixel coordinates (top-left of square)."""
    if flipped:
        col = 7 - col
        row = 7 - row
    px = cfg.BOARD_OFFSET_X + col * cfg.SQUARE_SIZE
    py = cfg.BOARD_OFFSET_Y + row * cfg.SQUARE_SIZE
    return (px, py)


def board_to_pixel_center(col, row, flipped=False):
    """Convert board coordinates to pixel center of square."""
    if flipped:
        col = 7 - col
        row = 7 - row
    px = cfg.BOARD_OFFSET_X + col * cfg.SQUARE_SIZE + cfg.SQUARE_SIZE // 2
    py = cfg.BOARD_OFFSET_Y + row * cfg.SQUARE_SIZE + cfg.SQUARE_SIZE // 2
    return (px, py)


def board_to_algebraic(col, row):
    """Convert board coordinates to algebraic notation (e.g., 'e4')."""
    return FILES[col] + RANKS[row]


def algebraic_to_board(notation):
    """Convert algebraic notation (e.g., 'e4') to board coordinates (col, row)."""
    if len(notation) != 2:
        return None
    col = FILES.find(notation[0])
    row = RANKS.find(notation[1])
    if col == -1 or row == -1:
        return None
    return (col, row)


def is_white_piece(piece):
    """Check if a piece character represents a white piece."""
    return piece != '.' and piece.isupper()


def is_black_piece(piece):
    """Check if a piece character represents a black piece."""
    return piece != '.' and piece.islower()


def is_enemy(piece, is_white_turn):
    """Check if a piece belongs to the opponent."""
    if piece == '.':
        return False
    if is_white_turn:
        return piece.islower()
    return piece.isupper()


def is_friendly(piece, is_white_turn):
    """Check if a piece belongs to the current player."""
    if piece == '.':
        return False
    if is_white_turn:
        return piece.isupper()
    return piece.islower()


def piece_name(piece_char):
    """Get the full name of a piece from its character."""
    names = {
        'K': 'King', 'Q': 'Queen', 'R': 'Rook',
        'B': 'Bishop', 'N': 'Knight', 'P': 'Pawn',
        'k': 'King', 'q': 'Queen', 'r': 'Rook',
        'b': 'Bishop', 'n': 'Knight', 'p': 'Pawn',
    }
    return names.get(piece_char, '')


def piece_color(piece_char):
    """Get the color string for a piece character."""
    if piece_char == '.':
        return None
    return 'white' if piece_char.isupper() else 'black'


def format_time(seconds):
    """Format seconds into MM:SS or H:MM:SS display string."""
    if seconds <= 0:
        return "0:00"
    total = int(seconds)
    if total >= 3600:
        h = total // 3600
        m = (total % 3600) // 60
        s = total % 60
        return f"{h}:{m:02d}:{s:02d}"
    else:
        m = total // 60
        s = total % 60
        return f"{m}:{s:02d}"


def format_time_precise(seconds):
    """Format time with tenths when under 30 seconds."""
    if seconds <= 0:
        return "0:00.0"
    if seconds < 30:
        m = int(seconds) // 60
        s = seconds % 60
        return f"{m}:{s:04.1f}"
    return format_time(seconds)


def deep_copy_board(board):
    """Create a deep copy of the board matrix."""
    return [row[:] for row in board]


def get_piece_image_name(piece_char):
    """Get the image filename for a piece character."""
    color = 'white' if piece_char.isupper() else 'black'
    names = {
        'k': 'king', 'q': 'queen', 'r': 'rook',
        'b': 'bishop', 'n': 'knight', 'p': 'pawn',
    }
    piece_type = names.get(piece_char.lower(), '')
    if piece_type:
        return f"{color}_{piece_type}.png"
    return None
