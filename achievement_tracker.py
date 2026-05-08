"""
achievement_tracker.py - Tracks and unlocks achievements
Hooks into game events (moves, game over) and checks conditions.
Works offline with local JSON storage, syncs to server when logged in.
"""

import json
import os
import time
from achievements import ACHIEVEMENTS, ACHIEVEMENTS_MAP

import config as cfg

LOCAL_FILE = os.path.join(cfg.DATA_DIR, "achievements_data.json")


class AchievementTracker:
    """Tracks game stats and unlocks achievements."""

    def __init__(self):
        # Persistent stats (saved locally)
        self.stats = {
            "games_played": 0,
            "games_won": 0,
            "win_streak": 0,
            "best_streak": 0,
            "total_captures": 0,
            "promotions": 0,
            "learned_sections": [],
        }
        self.unlocked = {}  # achievement_id -> timestamp
        self.pending_notifications = []  # newly unlocked, not yet shown

        # Per-game trackers (reset each game)
        self._game_promotions = 0
        self._game_was_checked = False
        self._game_pieces_lost = 0
        self._game_en_passant = False
        self._game_castled = False

        self._load_local()

    # -------------------------------------------------------------------
    # Local persistence
    # -------------------------------------------------------------------
    def _load_local(self):
        """Load achievements from local JSON file."""
        if os.path.exists(LOCAL_FILE):
            try:
                with open(LOCAL_FILE, 'r') as f:
                    data = json.load(f)
                self.stats = data.get("stats", self.stats)
                self.unlocked = data.get("unlocked", {})
            except Exception:
                pass

    def _save_local(self):
        """Save achievements to local JSON file."""
        try:
            data = {"stats": self.stats, "unlocked": self.unlocked}
            with open(LOCAL_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    # -------------------------------------------------------------------
    # Game lifecycle hooks
    # -------------------------------------------------------------------
    def on_game_start(self):
        """Reset per-game trackers."""
        self._game_promotions = 0
        self._game_was_checked = False
        self._game_pieces_lost = 0
        self._game_en_passant = False
        self._game_castled = False

    def on_move(self, move, engine, is_player_move=True):
        """Called after every move. Checks move-based achievements."""
        if not is_player_move:
            return

        # Track castling
        if move.is_castling:
            self._game_castled = True
            self._try_unlock("castle_builder")

        # Track en passant
        if move.is_en_passant:
            self._game_en_passant = True
            self._try_unlock("en_passant_master")

        # Track promotions
        if move.promotion:
            self._game_promotions += 1
            self.stats["promotions"] = self.stats.get("promotions", 0) + 1
            self._try_unlock("pawn_star")
            if self._game_promotions >= 3:
                self._try_unlock("promotion_army")

        # Track captures
        if move.captured:
            self.stats["total_captures"] = self.stats.get("total_captures", 0) + 1
            if move.captured.upper() == 'Q':
                self._try_unlock("queen_slayer")
            if self.stats["total_captures"] >= 50:
                self._try_unlock("material_hunter")

        # Track if player was put in check (opponent's move)
        if engine.is_check and is_player_move:
            pass  # Check is on opponent, not us

    def on_opponent_move(self, move, engine):
        """Called after opponent moves. Track if we're in check."""
        if engine.is_check:
            self._game_was_checked = True

        if move.captured:
            self._game_pieces_lost += 1

    def on_game_over(self, engine, player_won, player_is_white, time_control=""):
        """Called when game ends. Checks end-of-game achievements."""
        self.stats["games_played"] = self.stats.get("games_played", 0) + 1
        self._try_unlock("first_move")

        if self.stats["games_played"] >= 100:
            self._try_unlock("hundred_games")

        move_count = len(engine.move_history)

        if player_won:
            self.stats["games_won"] = self.stats.get("games_won", 0) + 1
            self.stats["win_streak"] = self.stats.get("win_streak", 0) + 1
            if self.stats["win_streak"] > self.stats.get("best_streak", 0):
                self.stats["best_streak"] = self.stats["win_streak"]

            self._try_unlock("first_victory")

            # Scholar's mate (win in 4 moves or fewer = 8 half-moves)
            if move_count <= 8:
                self._try_unlock("scholars_mate")

            # Clean sweep
            if self._game_pieces_lost == 0:
                self._try_unlock("clean_sweep")

            # Perfect game (never checked)
            if not self._game_was_checked:
                self._try_unlock("perfect_game")

            # Knight mate
            if engine.is_checkmate and engine.move_history:
                last_move = engine.move_history[-1]
                if last_move.piece.upper() == 'N':
                    self._try_unlock("knight_rider")

            # Back rank mate
            if engine.is_checkmate and engine.move_history:
                last_move = engine.move_history[-1]
                _, tr = last_move.to_sq
                if tr == 0 or tr == 7:
                    self._try_unlock("back_rank_mate")

            # Endgame expert (king + pawn vs king)
            if engine.is_checkmate:
                self._check_endgame_expert(engine, player_is_white)

            # Milestone wins
            if self.stats["games_won"] >= 10:
                self._try_unlock("ten_victories")
            if self.stats["games_won"] >= 50:
                self._try_unlock("fifty_victories")

            # Win streak
            if self.stats["win_streak"] >= 5:
                self._try_unlock("unbreakable")

            # Speed demon (bullet)
            if "1+0" in time_control or "Bullet" in time_control:
                self._try_unlock("speed_demon")

        else:
            self.stats["win_streak"] = 0

        # Marathon
        if move_count >= 100:
            self._try_unlock("marathon")

        # Check completionist
        total_possible = len(ACHIEVEMENTS) - 1  # minus completionist itself
        if len(self.unlocked) >= total_possible:
            self._try_unlock("completionist")

        self._save_local()

    def on_elo_update(self, new_elo):
        """Called when ELO changes."""
        if new_elo >= 1400:
            self._try_unlock("elo_rising")
        if new_elo >= 1800:
            self._try_unlock("grandmaster")
        self._save_local()

    def mark_section_learned(self, section_id):
        """Record that a lesson section has been learned."""
        learned = self.stats.get("learned_sections", [])
        if section_id not in learned:
            learned.append(section_id)
            self.stats["learned_sections"] = learned
            self._save_local()
            
            # Check Learn achievements
            self._try_unlock("first_lesson")
            
            from learn_data import get_total_sections
            total = get_total_sections()
            
            if len(learned) >= total / 2:
                self._try_unlock("halfway_there")
            if len(learned) >= total:
                self._try_unlock("chess_scholar")
                
            self._save_local()

    # -------------------------------------------------------------------
    # Double check detection (called from main game loop)
    # -------------------------------------------------------------------
    def check_double_check(self, engine, is_player_white):
        """Check if current position has double check (after player's move)."""
        if not engine.is_check:
            return
        # Count how many pieces attack the opponent king
        opp_white = not is_player_white
        king_pos = engine._find_king(opp_white)
        if not king_pos:
            return

        attackers = 0
        kc, kr = king_pos
        # Check all of player's pieces for attacks on king square
        for r in range(8):
            for c in range(8):
                p = engine.board[r][c]
                if p == '.' or p.isupper() == opp_white:
                    continue
                # Check if this piece attacks the king square
                if engine._is_piece_attacking(c, r, kc, kr):
                    attackers += 1

        if attackers >= 2:
            self._try_unlock("double_check")

    # -------------------------------------------------------------------
    # Fork detection
    # -------------------------------------------------------------------
    def check_knight_fork(self, engine, move, is_player_white):
        """Check if a knight move forks king and queen."""
        if move.piece.upper() != 'N':
            return

        tc, tr = move.to_sq
        king_char = 'k' if is_player_white else 'K'
        queen_char = 'q' if is_player_white else 'Q'

        attacks_king = False
        attacks_queen = False

        knight_offsets = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
        for dc, dr in knight_offsets:
            nc, nr = tc + dc, tr + dr
            if 0 <= nc < 8 and 0 <= nr < 8:
                target = engine.board[nr][nc]
                if target == king_char:
                    attacks_king = True
                elif target == queen_char:
                    attacks_queen = True

        if attacks_king and attacks_queen:
            self._try_unlock("fork_master")

    # -------------------------------------------------------------------
    # Internal
    # -------------------------------------------------------------------
    def _try_unlock(self, achievement_id):
        """Try to unlock an achievement. Adds to notifications if new."""
        if achievement_id in self.unlocked:
            return False
        if achievement_id not in ACHIEVEMENTS_MAP:
            return False

        self.unlocked[achievement_id] = time.time()
        self.pending_notifications.append(ACHIEVEMENTS_MAP[achievement_id])
        self._save_local()
        return True

    def _check_endgame_expert(self, engine, player_is_white):
        """Check if position is king+pawn vs king."""
        player_pieces = []
        opp_pieces = []
        for r in range(8):
            for c in range(8):
                p = engine.board[r][c]
                if p == '.':
                    continue
                if p.isupper() == player_is_white:
                    player_pieces.append(p.upper())
                else:
                    opp_pieces.append(p.upper())

        if sorted(player_pieces) == ['K', 'P'] and opp_pieces == ['K']:
            self._try_unlock("endgame_expert")

    def get_unlocked_list(self):
        """Get list of unlocked achievement dicts."""
        result = []
        for ach in ACHIEVEMENTS:
            if ach["id"] in self.unlocked:
                result.append({**ach, "unlocked_at": self.unlocked[ach["id"]]})
        return result

    def get_all_with_status(self):
        """Get all achievements with unlocked status."""
        result = []
        for ach in ACHIEVEMENTS:
            entry = {**ach}
            if ach["id"] in self.unlocked:
                entry["unlocked"] = True
                entry["unlocked_at"] = self.unlocked[ach["id"]]
            else:
                entry["unlocked"] = False
            result.append(entry)
        return result

    def get_progress(self):
        """Get progress fraction."""
        return len(self.unlocked), len(ACHIEVEMENTS)

    def pop_notification(self):
        """Pop the next pending notification, or None."""
        if self.pending_notifications:
            return self.pending_notifications.pop(0)
        return None
