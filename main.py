"""
main.py - Chess Game — Entry Point
Initializes Pygame, manages the game loop, handles events, and
orchestrates all game phases including online play.
"""

import pygame
import sys
import threading
import config as cfg
from config import (
    FPS, GAME_TITLE, BACKEND_API_URL,
    MODE_VS_AI, MODE_VS_PLAYER, MODE_ONLINE, MODE_LESSON,
    RESOLUTIONS, DISPLAY_MODES, SERVERS,
    recalculate_layout,
)
from game_engine import GameEngine
from ai_engine import AIEngine
from clock_manager import ChessClock
from sound_manager import SoundManager
from themes import ThemeManager
from game_state import GameStateManager
from renderer import Renderer
from ui_manager import UIManager
from utils import pixel_to_board
from achievement_tracker import AchievementTracker
from notification_manager import NotificationManager
from achievements import CATEGORIES
from auth_manager import AuthManager

class ChessGame:
    """Main game class managing the full application lifecycle."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((cfg.WINDOW_WIDTH, cfg.WINDOW_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)

        # Try to set icon
        try:
            icon = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.circle(icon, (212, 168, 67), (16, 16), 14)
            pygame.draw.circle(icon, (18, 18, 22), (16, 16), 10)
            pygame.display.set_icon(icon)
        except Exception:
            pass

        self.clock = pygame.time.Clock()

        # Core systems
        self.engine = GameEngine()
        self.ai = AIEngine()
        self.chess_clock = ChessClock()
        self.sound = SoundManager()
        self.sound.init()
        self.theme_manager = ThemeManager()
        self.state_manager = GameStateManager()
        self.renderer = Renderer(self.screen)
        self.ui = UIManager(self.screen, self.renderer)
        self.tracker = AchievementTracker()
        self.notifications = NotificationManager()
        
        self.auth = AuthManager(self.ui, self.tracker)
        self.auth.load_token()

        # Input handling state
        self.game_mode = MODE_VS_AI
        self.selected_square = None
        self.legal_moves = []
        self.dragging = False
        self.drag_piece = None
        self.drag_from = None
        self.drag_pos = (0, 0)
        self.last_move = None
        self.paused = False
        self.promoting = False
        self.promotion_move = None
        self.showing_game_over = False
        self.play_again_rect = None
        self.menu_rect = None

        # AI threading
        self.ai_thinking = False
        self.ai_move_result = None

        # Network
        from network_manager import NetworkManager
        self.network = NetworkManager()

        # Account text input focus
        self._active_field = "username"

        self.running = True

    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS)
            mouse_pos = pygame.mouse.get_pos()

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                self._handle_event(event, mouse_pos)

            self._update(dt, mouse_pos)
            self._draw(mouse_pos)

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def _handle_event(self, event, mouse_pos):
        """Route events to the current phase handler."""
        phase = self.ui.phase

        if phase == "splash":
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self.ui.transition_to("menu")

        elif phase == "menu":
            self._handle_menu_event(event, mouse_pos)

        elif phase == "settings":
            self._handle_settings_event(event, mouse_pos)

        elif phase == "setup":
            self._handle_setup_event(event, mouse_pos)

        elif phase == "online_menu":
            self._handle_online_menu_event(event, mouse_pos)

        elif phase == "achievements":
            self._handle_achievements_event(event, mouse_pos)

        elif phase == "account":
            self._handle_account_event(event, mouse_pos)

        elif phase == "learn_menu":
            self._handle_learn_menu_event(event, mouse_pos)

        elif phase == "lesson":
            self._handle_lesson_event(event, mouse_pos)

        elif phase == "playing":
            # Block input during AI animation
            if self.renderer.animation.active:
                return

            if self.paused:
                self._handle_pause_event(event, mouse_pos)
            elif self.promoting:
                self._handle_promotion_event(event, mouse_pos)
            elif self.showing_game_over:
                self._handle_game_over_event(event, mouse_pos)
            else:
                self._handle_game_event(event, mouse_pos)

    def _handle_menu_event(self, event, mouse_pos):
        """Handle main menu events."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            actions = self.ui.draw_main_menu(mouse_pos)
            
            if "vs_ai" in actions and actions["vs_ai"].collidepoint(mouse_pos):
                self.ui.game_mode = MODE_VS_AI
                self.sound.play('ui_click')
                self.ui.transition_to("setup")
            elif "vs_player" in actions and actions["vs_player"].collidepoint(mouse_pos):
                self.ui.game_mode = MODE_VS_PLAYER
                self.sound.play('ui_click')
                self.ui.transition_to("setup")
            elif "chess960_vs_ai" in actions and actions["chess960_vs_ai"].collidepoint(mouse_pos):
                self.ui.game_mode = MODE_VS_AI
                self.ui.game_variant = "Chess960"
                self.sound.play('ui_click')
                self.ui.transition_to("setup")
            elif "chess960_vs_player" in actions and actions["chess960_vs_player"].collidepoint(mouse_pos):
                self.ui.game_mode = MODE_VS_PLAYER
                self.ui.game_variant = "Chess960"
                self.sound.play('ui_click')
                self.ui.transition_to("setup")
            elif "online" in actions and actions["online"].collidepoint(mouse_pos):
                self.sound.play('ui_click')
                self.auth.fetch_leaderboard()  # Load ranking immediately
                self.ui.transition_to("online_menu")
            elif "learn" in actions and actions["learn"].collidepoint(mouse_pos):
                self.sound.play('ui_click')
                self.ui.transition_to("learn_menu")
            elif "achievements" in actions and actions["achievements"].collidepoint(mouse_pos):
                self.sound.play('ui_click')
                self.ui.transition_to("achievements")
            elif "settings" in actions and actions["settings"].collidepoint(mouse_pos):
                self.sound.play('ui_click')
                self.ui.transition_to("settings")
            elif "account" in actions and actions["account"].collidepoint(mouse_pos):
                self.sound.play('ui_click')
                self.ui.transition_to("account")
            elif "quit" in actions and actions["quit"].collidepoint(mouse_pos):
                self.running = False

    def _handle_settings_event(self, event, mouse_pos):
        """Handle settings screen events."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.ui.transition_to("menu")
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            rects = self.ui.draw_settings_screen(mouse_pos, self.sound)

            # Resolutions
            for res_name in RESOLUTIONS:
                key = f"res_{res_name}"
                if key in rects and rects[key].collidepoint(mouse_pos):
                    if res_name != self.ui.resolution:
                        self.ui.resolution = res_name
                        self._apply_resolution()
                        self.sound.play('ui_click')
                    return

            # Display modes
            for mode in DISPLAY_MODES:
                key = f"dmode_{mode}"
                if key in rects and rects[key].collidepoint(mouse_pos):
                    if mode != self.ui.display_mode:
                        self.ui.display_mode = mode
                        self._apply_display_mode()
                        self.sound.play('ui_click')
                    return

            # Board themes
            for theme_name in list(self._get_themes()):
                key = f"theme_{theme_name}"
                if key in rects and rects[key].collidepoint(mouse_pos):
                    self.ui.board_theme = theme_name
                    self.theme_manager.set_theme(theme_name)
                    self.sound.play('ui_click')
                    return

            # Toggles
            if "toggle_sound" in rects and rects["toggle_sound"].collidepoint(mouse_pos):
                self.ui.sound_enabled = not self.ui.sound_enabled
                self.sound.enabled = self.ui.sound_enabled
                self.sound.play('ui_click')
                return
            if "toggle_legal_moves" in rects and rects["toggle_legal_moves"].collidepoint(mouse_pos):
                self.ui.show_legal_moves = not self.ui.show_legal_moves
                self.sound.play('ui_click')
                return
            if "toggle_coordinates" in rects and rects["toggle_coordinates"].collidepoint(mouse_pos):
                self.ui.show_coordinates = not self.ui.show_coordinates
                self.sound.play('ui_click')
                return

            # Back
            if "back" in rects and rects["back"].collidepoint(mouse_pos):
                self.sound.play('ui_click')
                self.ui.transition_to("menu")
                return

    def _handle_setup_event(self, event, mouse_pos):
        """Handle setup screen events."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.ui.transition_to("menu")
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            rects = self.ui.draw_setup_screen(mouse_pos)

            for tc_name in list(self._get_time_controls()):
                key = f"tc_{tc_name}"
                if key in rects and rects[key].collidepoint(mouse_pos):
                    self.ui.time_control = tc_name
                    self.sound.play('ui_click')
                    return

            for diff_name in list(self._get_difficulties()):
                key = f"diff_{diff_name}"
                if key in rects and rects[key].collidepoint(mouse_pos):
                    self.ui.ai_difficulty = diff_name
                    self.sound.play('ui_click')
                    return

            from config import VARIANTS
            for v_name in VARIANTS:
                key = f"variant_{v_name}"
                if key in rects and rects[key].collidepoint(mouse_pos):
                    self.ui.game_variant = v_name
                    self.sound.play('ui_click')
                    return

            if "play_white" in rects and rects["play_white"].collidepoint(mouse_pos):
                self.ui.player_is_white = True
                self.sound.play('ui_click')
                return
            if "play_black" in rects and rects["play_black"].collidepoint(mouse_pos):
                self.ui.player_is_white = False
                self.sound.play('ui_click')
                return

            if rects["back"].collidepoint(mouse_pos):
                self.sound.play('ui_click')
                self.ui.transition_to("menu")
                return

            if rects["start"].collidepoint(mouse_pos):
                self.sound.play('ui_click')
                self._start_new_game()
                return

    def _handle_online_menu_event(self, event, mouse_pos):
        """Handle online menu events."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.ui.transition_to("menu")
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            rects = self.ui.draw_online_menu(mouse_pos, self.auth)

            # Game variant selection
            from config import VARIANTS
            for v_name in VARIANTS:
                key = f"variant_{v_name}"
                if key in rects and rects[key].collidepoint(mouse_pos):
                    self.ui.game_variant = v_name
                    self.sound.play('ui_click')
                    return

            if "back" in rects and rects["back"].collidepoint(mouse_pos):
                self.sound.play('ui_click')
                self.ui.transition_to("menu")
                return

            if "find_game" in rects and rects["find_game"].collidepoint(mouse_pos):
                self.sound.play('ui_click')
                if not self.ui.logged_in or not self.ui.auth_token:
                    self.ui.online_status = "Please login first!"
                    return
                    
                self.ui.online_status = "Searching for opponent..."
                from config import SERVERS, DEFAULT_SERVER
                srv = SERVERS.get(DEFAULT_SERVER, SERVERS["Frankfurt"])
                self.network.connect(srv["host"], 8000, self.ui.auth_token, self.ui.game_variant)
                return

            if "create_room" in rects and rects["create_room"].collidepoint(mouse_pos):
                self.sound.play('ui_click')
                self.ui.online_status = "Creating room..."
                # TODO: Create room via network_manager
                return

    def _handle_achievements_event(self, event, mouse_pos):
        """Handle achievements screen events."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.ui.transition_to("menu")
            return

        # Scroll with mouse wheel
        if event.type == pygame.MOUSEWHEEL:
            self.ui.ach_scroll = max(0, self.ui.ach_scroll - event.y * 30)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            rects = self.ui.draw_achievements_screen(mouse_pos, self.tracker)

            # Category tabs
            for cat in CATEGORIES:
                key = f"cat_{cat}"
                if key in rects and rects[key].collidepoint(mouse_pos):
                    self.ui.ach_category = cat
                    self.ui.ach_scroll = 0
                    self.sound.play('ui_click')
                    return

            if "back" in rects and rects["back"].collidepoint(mouse_pos):
                self.sound.play('ui_click')
                self.ui.transition_to("menu")
                return

    def _handle_account_event(self, event, mouse_pos):
        """Handle account screen events."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.ui.transition_to("menu")
            return

        if event.type == pygame.KEYDOWN:
            # Text input for username/password
            if self._active_field == "username":
                if event.key == pygame.K_BACKSPACE:
                    self.ui.input_username = self.ui.input_username[:-1]
                elif event.key == pygame.K_TAB:
                    self._active_field = "password"
                elif event.key == pygame.K_RETURN:
                    self._submit_account()
                elif event.unicode and len(self.ui.input_username) < 32:
                    self.ui.input_username += event.unicode
            elif self._active_field == "password":
                if event.key == pygame.K_BACKSPACE:
                    self.ui.input_password = self.ui.input_password[:-1]
                elif event.key == pygame.K_TAB:
                    self._active_field = "username"
                elif event.key == pygame.K_RETURN:
                    self._submit_account()
                elif event.unicode and len(self.ui.input_password) < 64:
                    self.ui.input_password += event.unicode

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            rects = self.ui.draw_account_screen(mouse_pos)

            if "field_username" in rects and rects["field_username"].collidepoint(mouse_pos):
                self._active_field = "username"
                return
            if "field_password" in rects and rects["field_password"].collidepoint(mouse_pos):
                self._active_field = "password"
                return
            if "tab_login" in rects and rects["tab_login"].collidepoint(mouse_pos):
                self.ui.account_mode = "login"
                self.ui.account_error = ""
                self.sound.play('ui_click')
                return
            if "tab_register" in rects and rects["tab_register"].collidepoint(mouse_pos):
                self.ui.account_mode = "register"
                self.ui.account_error = ""
                self.sound.play('ui_click')
                return
            if "submit" in rects and rects["submit"].collidepoint(mouse_pos):
                self.sound.play('ui_click')
                self._submit_account()
                return
            if "logout" in rects and rects["logout"].collidepoint(mouse_pos):
                self.sound.play('ui_click')
                self.auth.clear_token()
                return
            if "back" in rects and rects["back"].collidepoint(mouse_pos):
                self.sound.play('ui_click')
                self.ui.transition_to("menu")
                return

    def _submit_account(self):
        """Submit login or register request to backend."""
        username = self.ui.input_username.strip()
        password = self.ui.input_password.strip()

        if not username or not password:
            self.ui.account_error = "Please fill in all fields"
            return
            
        threading.Thread(
            target=self.auth.login_or_register,
            args=(self.ui.account_mode, username, password),
            daemon=True
        ).start()

    def _handle_learn_menu_event(self, event, mouse_pos):
        """Handle learn menu events."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.ui.transition_to("menu")
            return

        if event.type == pygame.MOUSEWHEEL:
            self.ui.learn_scroll = max(0, self.ui.learn_scroll - event.y * 30)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            rects = self.ui.draw_learn_menu(mouse_pos, self.tracker)
            
            from learn_data import LEARN_CURRICULUM
            for chapter in LEARN_CURRICULUM:
                for section in chapter['sections']:
                    key = f"section_{section['id']}"
                    if key in rects and rects[key].collidepoint(mouse_pos):
                        self.ui.selected_chapter_id = chapter['id']
                        self.ui.selected_section = section
                        self.sound.play('ui_click')
                        self.ui.transition_to("lesson")
                        return

            if "back" in rects and rects["back"].collidepoint(mouse_pos):
                self.sound.play('ui_click')
                self.ui.transition_to("menu")
                return

    def _handle_lesson_event(self, event, mouse_pos):
        """Handle lesson reading events."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.ui.transition_to("learn_menu")
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            rects = self.ui.draw_lesson(mouse_pos)
            
            if "complete" in rects and rects["complete"].collidepoint(mouse_pos):
                self.sound.play('ui_click')
                self.ui.game_mode = MODE_LESSON
                self._start_new_game()
                return

            if "back" in rects and rects["back"].collidepoint(mouse_pos):
                self.sound.play('ui_click')
                self.ui.transition_to("learn_menu")
                return

    def _handle_game_event(self, event, mouse_pos):
        """Handle in-game events (click/drag pieces)."""
        if self.ai_thinking:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            y_start = self._get_button_y_start()
            btn_rects = self.ui.draw_game_buttons(mouse_pos, y_start, self.game_mode)
            for action, rect in btn_rects.items():
                if rect.collidepoint(mouse_pos):
                    self._handle_button_action(action)
                    return

            flipped = (not self.ui.player_is_white and self.game_mode != MODE_VS_PLAYER)
            board_pos = pixel_to_board(*mouse_pos, flipped=flipped)
            if board_pos:
                col, row = board_pos
                piece = self.engine.get_piece(col, row)

                if self.selected_square:
                    move_made = self._try_move(col, row)
                    if not move_made:
                        if piece != '.' and self._is_current_player_piece(piece):
                            self.selected_square = (col, row)
                            self.legal_moves = self.engine.get_legal_moves(col, row)
                            self.dragging = True
                            self.drag_piece = piece
                            self.drag_from = (col, row)
                            self.drag_pos = mouse_pos
                        else:
                            self.selected_square = None
                            self.legal_moves = []
                else:
                    if piece != '.' and self._is_current_player_piece(piece):
                        self.selected_square = (col, row)
                        self.legal_moves = self.engine.get_legal_moves(col, row)
                        self.dragging = True
                        self.drag_piece = piece
                        self.drag_from = (col, row)
                        self.drag_pos = mouse_pos

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.drag_pos = mouse_pos

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                flipped = (not self.ui.player_is_white and self.game_mode != MODE_VS_PLAYER)
                board_pos = pixel_to_board(*mouse_pos, flipped=flipped)
                if board_pos:
                    col, row = board_pos
                    if self.drag_from and (col, row) != self.drag_from:
                        self._try_move(col, row)
                self.dragging = False
                self.drag_piece = None
                self.drag_from = None

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.paused = True
            elif event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                if self.game_mode == MODE_VS_PLAYER:
                    self.state_manager.undo(self.engine)

    def _handle_pause_event(self, event, mouse_pos):
        """Handle pause menu events."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.paused = False
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            rects = self.ui.draw_pause_menu(mouse_pos)
            for action, rect in rects.items():
                if rect.collidepoint(mouse_pos):
                    self.sound.play('ui_click')
                    if action == "resume":
                        self.paused = False
                    elif action == "undo":
                        if self.game_mode != MODE_ONLINE:
                            self.state_manager.undo(self.engine)
                            self.selected_square = None
                            self.legal_moves = []
                            self.last_move = self.engine.move_history[-1] if self.engine.move_history else None
                        self.paused = False
                    elif action == "new_game":
                        self.paused = False
                        self._start_new_game()
                    elif action == "main_menu":
                        self.paused = False
                        self.chess_clock.stop()
                        if self.game_mode == MODE_ONLINE:
                            self.network.disconnect()
                        self.ui.transition_to("menu")
                    elif action == "quit":
                        self.running = False
                    return

    def _handle_promotion_event(self, event, mouse_pos):
        """Handle pawn promotion selection."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            options = self.renderer.draw_promotion_dialog(self.engine.white_turn)
            for rect, piece_char in options:
                if rect.collidepoint(mouse_pos):
                    for move in self.legal_moves:
                        if (move.to_sq == self.promotion_move.to_sq and
                                move.from_sq == self.promotion_move.from_sq and
                                move.promotion and
                                move.promotion.upper() == piece_char.upper()):
                            
                            # In online mode, inform server
                            if self.game_mode == MODE_ONLINE:
                                self.network.send_move({
                                    "from": move.from_sq,
                                    "to": move.to_sq,
                                    "promotion": move.promotion
                                })

                            self._execute_move(move, animate=True)
                            break
                    self.promoting = False
                    self.promotion_move = None
                    self.sound.play('promote')
                    return

    def _handle_game_over_event(self, event, mouse_pos):
        """Handle game over screen events."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.play_again_rect and self.play_again_rect.collidepoint(mouse_pos):
                self.sound.play('ui_click')
                self._start_new_game()
            elif self.menu_rect and self.menu_rect.collidepoint(mouse_pos):
                self.sound.play('ui_click')
                if self.game_mode == MODE_ONLINE:
                    self.network.disconnect()
                self.showing_game_over = False
                self.ui.transition_to("menu")

    def _try_move(self, to_col, to_row):
        """Try to make a move to (to_col, to_row). Returns True if successful."""
        for move in self.legal_moves:
            if move.to_sq == (to_col, to_row):
                if move.promotion:
                    self.promoting = True
                    self.promotion_move = move
                    return True
                
                # In online mode, inform server
                if self.game_mode == MODE_ONLINE:
                    # Apply move first to get the resulting board hash for synchronization
                    self._execute_move(move, animate=True, is_local_player=True)
                    self.network.send_move({
                        "from": move.from_sq,
                        "to": move.to_sq,
                        "promotion": move.promotion,
                        "board_hash": self.engine.get_fen() # Simple FEN as hash
                    })
                else:
                    self._execute_move(move, animate=True, is_local_player=True)
                return True
        return False

    def _execute_move(self, move, animate=False, is_local_player=False):
        """Execute a validated move. If animate=True, trigger slide animation."""
        self.state_manager.save_snapshot(self.engine)

        # Start animation BEFORE making the move (so we know the piece)
        if animate:
            flipped = (not self.ui.player_is_white and self.game_mode != MODE_VS_PLAYER)
            piece_char = self.engine.get_piece(*move.from_sq)
            if piece_char:
                self.renderer.animation.start(piece_char, move.from_sq, move.to_sq, flipped=flipped)

        self.engine.make_move(move)
        self.last_move = move
        self.selected_square = None
        self.legal_moves = []

        if self.game_mode == MODE_LESSON:
            from utils import board_to_algebraic
            from_str = board_to_algebraic(*move.from_sq)
            to_str = board_to_algebraic(*move.to_sq)
            played_move = from_str + to_str
            
            expected = []
            if self.ui.selected_section:
                expected = self.ui.selected_section.get("expected_moves", [])
                
            if self.lesson_step < len(expected):
                if played_move == expected[self.lesson_step]:
                    self.lesson_step += 1
                    self.sound.play('ui_click')
                    if self.lesson_step >= len(expected):
                        # Passed
                        self.tracker.mark_section_learned(self.ui.selected_section['id'])
                        self.ui.transition_to("learn_menu")
                        self.notifications.push({
                            "name": "Lesson Completed!",
                            "description": "You mastered this challenge.",
                            "rarity": "epic",
                            "icon": "🎓"
                        })
                    return
                else:
                    # Failed, undo
                    self.state_manager.undo(self.engine)
                    self.sound.play('error')
                    self.notifications.push({
                        "name": "Incorrect Move",
                        "description": "That is not the solution. Try again!",
                        "rarity": "common",
                        "icon": "❌"
                    })
                    return

        # Achievement tracking
        if is_local_player:
            self.tracker.on_move(move, self.engine, is_player_move=True)
            self.tracker.check_knight_fork(self.engine, move, self.ui.player_is_white)
        else:
            self.tracker.on_opponent_move(move, self.engine)

        # Sound (delayed slightly for animated moves to feel right)
        self.sound.play_move_sound(move)
        if self.engine.is_check:
            self.sound.play('check')

        if not self.engine.game_over:
            self.chess_clock.switch()

        if self.engine.game_over:
            self.chess_clock.stop()
            self.sound.play('game_over')
            self.showing_game_over = True
            # Track game over for achievements
            player_won = False
            if self.engine.winner:
                if self.ui.player_is_white and self.engine.winner == 'white':
                    player_won = True
                elif not self.ui.player_is_white and self.engine.winner == 'black':
                    player_won = True
            self.tracker.on_game_over(
                self.engine, player_won, self.ui.player_is_white,
                self.ui.time_control)
            
            # Online: inform server of final result
            if self.game_mode == MODE_ONLINE:
                self.network.send_game_over({
                    "winner": self.engine.winner,
                    "reason": self.engine.game_over_reason
                })
            return

        if (self.game_mode == MODE_VS_AI and
                not self.engine.game_over and
                self._is_ai_turn()):
            self._start_ai_move()

    def _start_ai_move(self):
        """Start AI computation in a background thread."""
        self.ai_thinking = True

        def ai_compute():
            move = self.ai.get_best_move(self.engine)
            self.ai_move_result = move

        thread = threading.Thread(target=ai_compute, daemon=True)
        thread.start()

    def _is_ai_turn(self):
        """Check if it's the AI's turn."""
        if self.game_mode != MODE_VS_AI:
            return False
        if self.ui.player_is_white:
            return not self.engine.white_turn
        return self.engine.white_turn

    def _is_current_player_piece(self, piece):
        """Check if a piece belongs to the current player."""
        if self.game_mode == MODE_VS_AI and self._is_ai_turn():
            return False
        
        # In online mode, you can only move your assigned color
        if self.game_mode == MODE_ONLINE:
            if self.ui.player_is_white:
                return piece.isupper() and self.engine.white_turn
            else:
                return piece.islower() and not self.engine.white_turn

        if self.engine.white_turn:
            return piece.isupper()
        return piece.islower()

    def _start_new_game(self, skip_reset=False):
        """Initialize a new game with current settings."""
        self.game_mode = self.ui.game_mode
        if not skip_reset:
            is_960 = (self.ui.game_variant == "Chess960")
            self.engine.reset(is_960=is_960)
        
        self.ai.set_difficulty(self.ui.ai_difficulty)
        self.chess_clock.set_time_control(self.ui.time_control)
        self.chess_clock.reset()
        self.theme_manager.set_theme(self.ui.board_theme)
        self.state_manager.reset()

        self.selected_square = None
        self.legal_moves = []
        self.last_move = None
        self.paused = False
        self.promoting = False
        self.showing_game_over = False
        self.ai_thinking = False
        self.ai_move_result = None
        self.lesson_step = 0

        if self.ui.game_mode == MODE_LESSON and self.ui.selected_section:
            fen = self.ui.selected_section.get("challenge_fen")
            if fen:
                self.engine.load_fen(fen)
                # Ensure no expected moves means instant completion on Start
                expected = self.ui.selected_section.get("expected_moves", [])
                if not expected:
                    self.tracker.mark_section_learned(self.ui.selected_section['id'])
                    self.ui.transition_to("learn_menu")
                    self.notifications.push({
                        "name": "Lesson Completed!",
                        "description": "You finished reading the lesson.",
                        "rarity": "epic",
                        "icon": "🎓"
                    })
                    return

        self.ui.phase = "playing"
        self.ui.fading_in = True
        self.ui.transition_alpha = 255

        self.chess_clock.start(self.engine.white_turn)
        self.tracker.on_game_start()

        if self.game_mode == MODE_VS_AI and self._is_ai_turn():
            self._start_ai_move()

    def _handle_button_action(self, action):
        """Handle gameplay button presses."""
        self.sound.play('ui_click')
        if action == "pause":
            self.paused = True
        elif action == "new_game":
            self._start_new_game()
        elif action == "undo":
            self.state_manager.undo(self.engine)
            self.selected_square = None
            self.legal_moves = []
            self.last_move = self.engine.move_history[-1] if self.engine.move_history else None
        elif action == "resign":
            if self.game_mode == MODE_ONLINE:
                self.network.send_resign()
            
            self.engine.resign()
            self.chess_clock.stop()
            self.sound.play('game_over')
            self.showing_game_over = True

    def _apply_resolution(self):
        """Apply resolution change — recalculates entire layout."""
        res = RESOLUTIONS.get(self.ui.resolution, (cfg.WINDOW_WIDTH, cfg.WINDOW_HEIGHT))
        w, h = res
        flags = 0
        if self.ui.display_mode == "Fullscreen":
            flags = pygame.FULLSCREEN
        elif self.ui.display_mode == "Borderless":
            flags = pygame.NOFRAME
        self.screen = pygame.display.set_mode((w, h), flags)

        # Recalculate all layout globals
        recalculate_layout(w, h)

        # Re-scale renderer assets (background, pieces)
        self.renderer.resize(self.screen)
        self.ui.screen = self.screen

    def _apply_display_mode(self):
        """Apply display mode change."""
        self._apply_resolution()

    def _get_button_y_start(self):
        return cfg.WINDOW_HEIGHT - 200

    def _process_network_events(self):
        """Process incoming events from the network manager."""
        events = self.network.poll_events()
        for event in events:
            if event["type"] == "match_found":
                self.ui.online_status = "Match Found!"
                self.sound.play('ui_click')
                
                # Setup online game parameters
                self.game_mode = MODE_ONLINE
                self.ui.game_mode = MODE_ONLINE
                self.ui.player_is_white = (event["color"] == "white")
                self.ui.time_control = "Rapid 10+0"
                self.network.opponent_name = event["opponent"]
                self.network.opponent_elo = event.get("opponent_elo", 1200)
                
                # Synchronize variant and seed
                is_960 = (event.get("variant") == "Chess960")
                self.ui.game_variant = event.get("variant", "Standard")
                seed = event.get("seed")
                
                # Reset engine with synced data
                self.engine.reset(is_960=is_960, seed=seed)
                
                # Reset local state
                self.selected_square = None
                self.legal_moves = []
                self.last_move = None
                
                # Start game!
                self._start_new_game(skip_reset=True)
                
            elif event["type"] == "move" and self.ui.phase == "playing":
                move_dict = event["move"]
                # Convert network dict move back to engine move representation
                from_sq = tuple(move_dict["from"])
                to_sq = tuple(move_dict["to"])
                
                applied = False
                for m in self.engine.get_all_legal_moves(self.engine.white_turn):
                    if m.from_sq == from_sq and m.to_sq == to_sq:
                        # Check promotion
                        if m.promotion and "promotion" in move_dict:
                            m.promotion = move_dict["promotion"]
                        
                        # Apply move
                        self._execute_move(m, animate=True, is_local_player=False)
                        applied = True
                        
                        # Check for board state desync
                        remote_hash = move_dict.get("board_hash")
                        if remote_hash and remote_hash != self.engine.get_fen():
                            print(f"[Online] Desync detected! Local: {self.engine.get_fen()}, Remote: {remote_hash}")
                            self.network.request_sync()
                        break
                
                if not applied:
                    # Illegal move or desync, request full state
                    print(f"[Online] Received illegal move {from_sq}->{to_sq}. Requesting sync.")
                    self.network.request_sync()

            elif event["type"] == "request_sync":
                # Opponent requested our state
                self.network.send_sync(self.engine.get_fen())

            elif event["type"] == "sync_state":
                # Opponent sent their state
                print(f"[Online] Reconciling board state via FEN sync.")
                self.engine.load_fen(event["fen"])
                self.last_move = None # Clear highlight as it might be invalid now
                self.selected_square = None
                self.legal_moves = []
                        
            elif event["type"] == "resign" and self.ui.phase == "playing":
                self.engine.game_over = True
                self.engine.winner = event.get("winner")
                self.engine.game_over_reason = "by resignation"
                self.chess_clock.stop()
                self.showing_game_over = True
            
            elif event["type"] == "game_over" and self.ui.phase == "playing":
                # Server decided game is over (e.g. timeout detected by server or reported by other)
                self.engine.game_over = True
                self.engine.winner = event.get("winner")
                self.engine.game_over_reason = event.get("reason", "unknown")
                self.chess_clock.stop()
                self.showing_game_over = True
                
            elif event["type"] == "connection_error":
                self.ui.online_status = "Error: " + event.get("message", "")
                self.network.disconnect()

    def _update(self, dt, mouse_pos):
        """Update game logic."""
        self.ui.update_transition()

        # AI move completion — execute with animation
        if self.ai_thinking and self.ai_move_result is not None:
            move = self.ai_move_result
            self.ai_move_result = None
            self.ai_thinking = False
            if move:
                self._execute_move(move, animate=True)

        # Update animation
        if self.renderer.animation.active:
            self.renderer.animation.update()

        # Process network events
        if self.network.connected or getattr(self.network, '_running', False):
            self._process_network_events()

        # Clock
        if (self.ui.phase == "playing" and not self.paused and
                not self.engine.game_over and not self.promoting):
            timeout = self.chess_clock.update()
            if timeout:
                is_white_timeout = self.chess_clock.white_timed_out
                self.engine.timeout(is_white_timeout)
                self.sound.play('game_over')
                self.showing_game_over = True

        # Achievement notifications
        notif = self.tracker.pop_notification()
        if notif:
            self.notifications.push(notif)
            self.auth.sync_achievements()
        self.notifications.update()

    def _draw(self, mouse_pos):
        """Draw the current frame based on phase."""
        phase = self.ui.phase

        if phase == "splash":
            done = self.ui.draw_splash(self.clock.get_time())
            if done and not self.ui.fading_out:
                self.ui.transition_to("menu")

        elif phase == "menu":
            self.ui.draw_main_menu(mouse_pos)

        elif phase == "settings":
            self.ui.draw_settings_screen(mouse_pos, self.sound)

        elif phase == "setup":
            self.ui.draw_setup_screen(mouse_pos)

        elif phase == "online_menu":
            self.ui.draw_online_menu(mouse_pos, self.auth)

        elif phase == "achievements":
            self.ui.draw_achievements_screen(mouse_pos, self.tracker)

        elif phase == "account":
            self.ui.draw_account_screen(mouse_pos)

        elif phase == "learn_menu":
            self.ui.draw_learn_menu(mouse_pos, self.tracker)

        elif phase == "lesson":
            self.ui.draw_lesson(mouse_pos)

        elif phase == "playing":
            self._draw_gameplay(mouse_pos)

        # Achievement toast notifications (always on top)
        self.notifications.draw(self.screen, self.renderer.fonts)

        self.ui.draw_transition()

    def _draw_gameplay(self, mouse_pos):
        """Draw the full gameplay screen."""
        self.renderer.draw_background()

        check_sq = None
        if self.engine.is_check:
            check_sq = self.engine._find_king(self.engine.white_turn)

        show_moves = self.legal_moves if (self.selected_square and
                                           self.ui.show_legal_moves) else None

        flipped = (not self.ui.player_is_white and self.game_mode != MODE_VS_PLAYER)

        self.renderer.draw_board(
            self.theme_manager,
            selected=self.selected_square,
            legal_moves=show_moves,
            last_move=self.last_move,
            check_square=check_sq,
            show_coordinates=self.ui.show_coordinates,
            flipped=flipped
        )

        self.renderer.draw_pieces(
            self.engine.board,
            dragging_piece=self.drag_piece if self.dragging else None,
            drag_pos=self.drag_pos if self.dragging else None,
            drag_from=self.drag_from if self.dragging else None,
            flipped=flipped
        )

        white_name, black_name = "WHITE", "BLACK"
        if self.game_mode == MODE_ONLINE:
            if self.ui.player_is_white:
                white_name, black_name = self.ui.username, self.network.opponent_name
            else:
                white_name, black_name = self.network.opponent_name, self.ui.username

        next_y = self.renderer.draw_clocks(self.chess_clock, y_offset=0, white_name=white_name, black_name=black_name)
        next_y = self.renderer.draw_captured_pieces(self.engine, next_y)

        history_height = self._get_button_y_start() - next_y - 16
        if history_height > 60:
            next_y = self.renderer.draw_move_history(self.engine, next_y,
                                                      max_height=history_height)

        self.renderer.draw_status_bar(self.engine, self.game_mode,
                                       cfg.WINDOW_HEIGHT - 30)

        btn_y = self._get_button_y_start()
        self.ui.draw_game_buttons(mouse_pos, btn_y, self.game_mode)

        if self.ai_thinking:
            self._draw_thinking_indicator()

        if self.game_mode == MODE_LESSON and self.ui.selected_section:
            instruction = self.ui.selected_section.get("instruction", "")
            if instruction:
                self.ui._draw_lesson_overlay(instruction)

        if self.promoting:
            self.renderer.draw_promotion_dialog(
                self.engine.white_turn if self.promotion_move is None
                else self.promotion_move.piece.isupper())

        if self.paused:
            self.ui.draw_pause_menu(mouse_pos)

        if self.showing_game_over:
            self.play_again_rect, self.menu_rect = \
                self.renderer.draw_game_over_overlay(self.engine)

    def _draw_thinking_indicator(self):
        """Draw AI thinking indicator."""
        dots = "." * (int(pygame.time.get_ticks() / 500) % 4)
        text = self.renderer.fonts['body'].render(
            f"AI thinking{dots}", True, (212, 168, 67))
        x = cfg.PANEL_X + 10
        y = cfg.WINDOW_HEIGHT - 55
        self.screen.blit(text, (x, y))

    def _get_time_controls(self):
        from config import TIME_CONTROLS
        return TIME_CONTROLS

    def _get_themes(self):
        from config import BOARD_THEMES
        return BOARD_THEMES

    def _get_difficulties(self):
        from config import AI_DIFFICULTIES
        return AI_DIFFICULTIES


if __name__ == "__main__":
    game = ChessGame()
    game.run()
