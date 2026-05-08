"""
game_state.py - Game State Management
Handles move history display, undo/redo, and future save/load support.
"""


class GameStateManager:
    """Manages game state, history tracking, and undo/redo."""

    def __init__(self):
        self.undo_stack = []  # Stores engine snapshots for undo
        self.redo_stack = []

    def reset(self):
        """Reset state tracking."""
        self.undo_stack.clear()
        self.redo_stack.clear()

    def save_snapshot(self, engine):
        """Save a snapshot of the engine state before a move."""
        from utils import deep_copy_board
        snapshot = {
            'board': deep_copy_board(engine.board),
            'white_turn': engine.white_turn,
            'move_history': [m for m in engine.move_history],
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
        self.undo_stack.append(snapshot)
        self.redo_stack.clear()

    def can_undo(self):
        return len(self.undo_stack) > 0

    def can_redo(self):
        return len(self.redo_stack) > 0

    def undo(self, engine):
        """Undo the last move by restoring a snapshot."""
        if not self.undo_stack:
            return False

        # Save current state for redo
        from utils import deep_copy_board
        current = {
            'board': deep_copy_board(engine.board),
            'white_turn': engine.white_turn,
            'move_history': [m for m in engine.move_history],
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
        self.redo_stack.append(current)

        # Restore snapshot
        snapshot = self.undo_stack.pop()
        self._restore_snapshot(engine, snapshot)
        return True

    def redo(self, engine):
        """Redo an undone move."""
        if not self.redo_stack:
            return False

        # Save current for undo
        from utils import deep_copy_board
        current = {
            'board': deep_copy_board(engine.board),
            'white_turn': engine.white_turn,
            'move_history': [m for m in engine.move_history],
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
        self.undo_stack.append(current)

        snapshot = self.redo_stack.pop()
        self._restore_snapshot(engine, snapshot)
        return True

    def _restore_snapshot(self, engine, snapshot):
        """Restore engine state from a snapshot dict."""
        engine.board = snapshot['board']
        engine.white_turn = snapshot['white_turn']
        engine.move_history = snapshot['move_history']
        engine.position_history = snapshot['position_history']
        engine.halfmove_clock = snapshot['halfmove_clock']
        engine.fullmove_number = snapshot['fullmove_number']
        engine.white_king_moved = snapshot['white_king_moved']
        engine.white_rook_a_moved = snapshot['white_rook_a_moved']
        engine.white_rook_h_moved = snapshot['white_rook_h_moved']
        engine.black_king_moved = snapshot['black_king_moved']
        engine.black_rook_a_moved = snapshot['black_rook_a_moved']
        engine.black_rook_h_moved = snapshot['black_rook_h_moved']
        engine.en_passant_target = snapshot['en_passant_target']
        engine.is_check = snapshot['is_check']
        engine.is_checkmate = snapshot['is_checkmate']
        engine.is_stalemate = snapshot['is_stalemate']
        engine.is_draw = snapshot['is_draw']
        engine.draw_reason = snapshot['draw_reason']
        engine.game_over = snapshot['game_over']
        engine.winner = snapshot['winner']
        engine.white_captured = snapshot['white_captured']
        engine.black_captured = snapshot['black_captured']
