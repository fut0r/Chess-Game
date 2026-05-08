"""
ui_manager.py - UI Manager for Menus, Phases, and Transitions
Uses self.screen.get_size() for all positioning so layout adapts to
any resolution. All corners sharp/boxed.
"""

import pygame
import time
import config as cfg
from config import (
    GAME_TITLE, GAME_VERSION, GAME_AUTHOR,
    COLOR_BG_DARK, COLOR_GOLD, COLOR_GOLD_DIM, COLOR_GOLD_BRIGHT,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_DIM,
    COLOR_BUTTON, COLOR_BUTTON_HOVER, COLOR_BUTTON_ACTIVE, COLOR_BORDER,
    COLOR_PANEL_BG, COLOR_OVERLAY,
    BOARD_THEMES, TIME_CONTROLS, AI_DIFFICULTIES,
    RESOLUTIONS, DISPLAY_MODES, SERVERS,
    MODE_VS_AI, MODE_VS_PLAYER, MODE_ONLINE,
    SPLASH_DURATION, FADE_SPEED,
    DEFAULT_RESOLUTION, DEFAULT_DISPLAY_MODE, DEFAULT_SERVER,
)
from achievements import ACHIEVEMENTS, CATEGORIES, RARITY_COLORS


class UIManager:
    """Manages all menu screens and game phase transitions."""

    def __init__(self, screen, renderer):
        self.screen = screen
        self.renderer = renderer

        self.phase = "splash"
        self.transition_alpha = 255
        self.fading_in = True
        self.fading_out = False
        self.next_phase = None
        self.splash_timer = 0

        # Selections
        self.game_mode = MODE_VS_AI
        self.game_variant = "Standard"
        self.ai_difficulty = "Medium"
        self.time_control = "Blitz 5+0"
        self.board_theme = "Classic"
        self.player_is_white = True
        self.sound_enabled = True
        self.show_legal_moves = True
        self.show_coordinates = True
        self.resolution = DEFAULT_RESOLUTION
        self.display_mode = DEFAULT_DISPLAY_MODE
        self.selected_server = DEFAULT_SERVER
        self.room_code = ""
        self.online_status = ""

        # Achievement screen
        self.ach_category = "All"
        self.ach_scroll = 0

        # Account
        self.logged_in = False
        self.username = ""
        self.auth_token = None
        self.account_mode = "login"  # 'login', 'register', 'profile'
        self.input_username = ""
        self.input_password = ""
        self.account_error = ""
        self.account_info = None  # user dict from API

        # Learn Chess
        self.selected_chapter_id = None
        self.selected_section = None  # Holds the section dict
        self.learn_scroll = 0

        # Overlays


    def _size(self):
        """Get current window size."""
        return self.screen.get_size()

    def transition_to(self, phase):
        self.fading_out = True
        self.next_phase = phase
        self.transition_alpha = 0

    def update_transition(self):
        if self.fading_in:
            self.transition_alpha -= FADE_SPEED
            if self.transition_alpha <= 0:
                self.transition_alpha = 0
                self.fading_in = False
            return True
        if self.fading_out:
            self.transition_alpha += FADE_SPEED
            if self.transition_alpha >= 255:
                self.transition_alpha = 255
                self.phase = self.next_phase
                self.fading_out = False
                self.fading_in = True
                self.next_phase = None
            return True
        return False

    def draw_transition(self):
        if self.transition_alpha > 0:
            W, H = self._size()
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, min(255, self.transition_alpha)))
            self.screen.blit(ov, (0, 0))

    # -------------------------------------------------------------------
    # SPLASH
    # -------------------------------------------------------------------
    def draw_splash(self, dt):
        W, H = self._size()
        self.renderer.draw_background()
        self.splash_timer += dt
        alpha = min(255, int(self.splash_timer * 0.3))

        title = self.renderer.fonts['splash_title'].render("CHESS GAME", True, COLOR_GOLD)
        title.set_alpha(alpha)
        tx, ty = (W - title.get_width()) // 2, H // 2 - 60
        self.screen.blit(title, (tx, ty))

        lw = min(260, int(self.splash_timer * 0.4))
        if lw > 0:
            lx = (W - lw) // 2
            pygame.draw.line(self.screen, COLOR_GOLD_DIM, (lx, ty+65), (lx+lw, ty+65), 1)

        sub = self.renderer.fonts['splash_sub'].render(f"by {GAME_AUTHOR}", True, COLOR_TEXT_SECONDARY)
        sub.set_alpha(min(255, max(0, alpha - 80)))
        self.screen.blit(sub, ((W - sub.get_width()) // 2, ty + 80))

        if self.splash_timer > 1500 and (self.splash_timer // 500) % 2 == 0:
            hint = self.renderer.fonts['body_small'].render("Press any key to continue", True, COLOR_TEXT_DIM)
            self.screen.blit(hint, ((W - hint.get_width()) // 2, H - 80))

        return self.splash_timer >= SPLASH_DURATION

    # -------------------------------------------------------------------
    # MAIN MENU
    # -------------------------------------------------------------------
    def draw_main_menu(self, mouse_pos):
        W, H = self._size()
        self.renderer.draw_background()

        title = self.renderer.fonts['title'].render("CHESS GAME", True, COLOR_GOLD)
        self.screen.blit(title, ((W - title.get_width()) // 2, int(H * 0.07)))

        lw = 180
        ly = int(H * 0.07) + title.get_height() + 8
        pygame.draw.line(self.screen, COLOR_GOLD_DIM,
                         ((W - lw) // 2, ly), ((W + lw) // 2, ly), 1)

        btn_w, btn_h = min(320, int(W * 0.25)), 45
        bx = (W - btn_w) // 2
        start_y = ly + 20
        gap = 10

        buttons = [("Play vs AI", "vs_ai"), ("Play vs Player", "vs_player"),
                   ("Play Online", "online"), ("Learn Chess", "learn"), 
                   ("Achievements", "achievements"), ("Settings", "settings"), 
                   ("Account", "account"), ("Quit", "quit")]
        actions = {}
        for i, (label, action) in enumerate(buttons):
            by = start_y + i * (btn_h + gap)
            rect = pygame.Rect(bx, by, btn_w, btn_h)
            self.renderer.draw_button(label, rect, hover=rect.collidepoint(mouse_pos))
            actions[action] = rect




        ver = self.renderer.fonts['body_small'].render(
            f"v{GAME_VERSION}  |  {GAME_AUTHOR}", True, COLOR_TEXT_DIM)
        self.screen.blit(ver, ((W - ver.get_width()) // 2, H - 40))
        return actions

    # -------------------------------------------------------------------
    # SETTINGS
    # -------------------------------------------------------------------
    def draw_settings_screen(self, mouse_pos, sound_manager=None):
        W, H = self._size()
        self.renderer.draw_background()

        title = self.renderer.fonts['heading'].render("SETTINGS", True, COLOR_GOLD)
        self.screen.blit(title, ((W - title.get_width()) // 2, 30))

        rects = {}
        col_w = min(380, int(W * 0.28))
        col1_x = W // 2 - col_w - 20
        col2_x = W // 2 + 20
        btn_h, gap = 40, 8
        y = 75

        # Left column — Display
        self._section("DISPLAY", col1_x, y); y += 28
        for rn in RESOLUTIONS:
            r = pygame.Rect(col1_x, y, col_w, btn_h)
            self.renderer.draw_button(rn, r, hover=r.collidepoint(mouse_pos),
                                       active=(rn == self.resolution), small=True)
            rects[f"res_{rn}"] = r; y += btn_h + gap
        y += 10
        self._section("DISPLAY MODE", col1_x, y); y += 28
        for mode in DISPLAY_MODES:
            r = pygame.Rect(col1_x, y, col_w, btn_h)
            self.renderer.draw_button(mode, r, hover=r.collidepoint(mouse_pos),
                                       active=(mode == self.display_mode), small=True)
            rects[f"dmode_{mode}"] = r; y += btn_h + gap

        # Right column — Theme & Audio
        y = 75
        self._section("BOARD THEME", col2_x, y); y += 28
        for tn in BOARD_THEMES:
            r = pygame.Rect(col2_x, y, col_w, btn_h)
            self.renderer.draw_button(tn, r, hover=r.collidepoint(mouse_pos),
                                       active=(tn == self.board_theme), small=True)
            th = BOARD_THEMES[tn]; ps = 16; px = col2_x + col_w - 50; pyc = y + (btn_h - ps) // 2
            pygame.draw.rect(self.screen, th["light"], (px, pyc, ps, ps))
            pygame.draw.rect(self.screen, th["dark"], (px + ps + 2, pyc, ps, ps))
            rects[f"theme_{tn}"] = r; y += btn_h + gap
        y += 10
        self._section("AUDIO & GAMEPLAY", col2_x, y); y += 28
        for key, label, val in [
            ("toggle_sound", f"Sound Effects:  {'ON' if self.sound_enabled else 'OFF'}", self.sound_enabled),
            ("toggle_legal_moves", f"Show Legal Moves:  {'ON' if self.show_legal_moves else 'OFF'}", self.show_legal_moves),
            ("toggle_coordinates", f"Show Coordinates:  {'ON' if self.show_coordinates else 'OFF'}", self.show_coordinates),
        ]:
            r = pygame.Rect(col2_x, y, col_w, btn_h)
            self.renderer.draw_button(label, r, hover=r.collidepoint(mouse_pos),
                                       active=val, small=True)
            rects[key] = r; y += btn_h + gap

        # Back
        bw, bh = 200, 50
        br = pygame.Rect((W - bw) // 2, H - 70, bw, bh)
        self.renderer.draw_button("Back", br, hover=br.collidepoint(mouse_pos))
        rects["back"] = br
        return rects

    # -------------------------------------------------------------------
    # GAME SETUP
    # -------------------------------------------------------------------
    def draw_setup_screen(self, mouse_pos):
        W, H = self._size()
        self.renderer.draw_background()

        from config import GAME_MODES
        mt = next((m["name"] for m in GAME_MODES if m["id"] == self.game_mode), "UNKNOWN MODE").upper()
        title = self.renderer.fonts['heading'].render(f"GAME SETUP  -  {mt}", True, COLOR_GOLD)
        self.screen.blit(title, ((W - title.get_width()) // 2, 30))

        rects = {}
        col_w = min(380, int(W * 0.28))
        col1_x = W // 2 - col_w - 20
        col2_x = W // 2 + 20
        btn_h, gap = 40, 8

        # Left — Time Control
        y = 80
        self._section("TIME CONTROL", col1_x, y); y += 30
        for tc in TIME_CONTROLS:
            r = pygame.Rect(col1_x, y, col_w, btn_h)
            self.renderer.draw_button(tc, r, hover=r.collidepoint(mouse_pos),
                                       active=(tc == self.time_control), small=True)
            rects[f"tc_{tc}"] = r; y += btn_h + gap

        # Right — Variant & AI Difficulty
        yr = 80
        from config import MODE_VS_AI, VARIANTS
        self._section("GAME VARIANT", col2_x, yr); yr += 30
        for v in VARIANTS:
            r = pygame.Rect(col2_x, yr, col_w, btn_h)
            self.renderer.draw_button(v, r, hover=r.collidepoint(mouse_pos),
                                       active=(v == self.game_variant), small=True)
            rects[f"variant_{v}"] = r; yr += btn_h + gap
            
        yr += 16
        
        if self.game_mode == MODE_VS_AI:
            self._section("AI DIFFICULTY", col2_x, yr); yr += 30
            for d in AI_DIFFICULTIES:
                r = pygame.Rect(col2_x, yr, col_w, btn_h)
                self.renderer.draw_button(d, r, hover=r.collidepoint(mouse_pos),
                                           active=(d == self.ai_difficulty), small=True)
                rects[f"diff_{d}"] = r; yr += btn_h + gap
            yr += 16
            self._section("PLAY AS", col2_x, yr); yr += 30
            hw = (col_w - gap) // 2
            wr = pygame.Rect(col2_x, yr, hw, btn_h)
            br = pygame.Rect(col2_x + hw + gap, yr, hw, btn_h)
            self.renderer.draw_button("White", wr, hover=wr.collidepoint(mouse_pos),
                                       active=self.player_is_white, small=True)
            self.renderer.draw_button("Black", br, hover=br.collidepoint(mouse_pos),
                                       active=not self.player_is_white, small=True)
            rects["play_white"] = wr; rects["play_black"] = br

        # Bottom
        bw, bh, g = 200, 50, 20
        total = bw * 2 + g
        bx1 = (W - total) // 2
        by = H - 80
        back_r = pygame.Rect(bx1, by, bw, bh)
        start_r = pygame.Rect(bx1 + bw + g, by, bw, bh)
        self.renderer.draw_button("Back", back_r, hover=back_r.collidepoint(mouse_pos))
        self.renderer.draw_button("Start Game", start_r, hover=start_r.collidepoint(mouse_pos), active=True)
        rects["back"] = back_r; rects["start"] = start_r
        return rects

    # -------------------------------------------------------------------
    # ONLINE MENU
    # -------------------------------------------------------------------
    def draw_online_menu(self, mouse_pos):
        W, H = self._size()
        self.renderer.draw_background()

        title = self.renderer.fonts['heading'].render("PLAY ONLINE", True, COLOR_GOLD)
        self.screen.blit(title, ((W - title.get_width()) // 2, 30))

        rects = {}
        col_w = min(400, int(W * 0.3))
        left_x = (W - col_w) // 2
        btn_h, gap = 44, 10
        y = 80

        self._section("GAME VARIANT", left_x, y); y += 30
        from config import VARIANTS
        for v in VARIANTS:
            r = pygame.Rect(left_x, y, col_w, btn_h)
            self.renderer.draw_button(v, r, hover=r.collidepoint(mouse_pos),
                                       active=(v == self.game_variant), small=True)
            rects[f"variant_{v}"] = r; y += btn_h + gap
        y += 20

        if self.online_status:
            st = self.renderer.fonts['body'].render(self.online_status, True, COLOR_GOLD)
            self.screen.blit(st, ((W - st.get_width()) // 2, H - 130))

        bw, bh, g = 200, 50, 20
        total = bw * 2 + g
        bx1 = (W - total) // 2
        by = H - 70
        back_r = pygame.Rect(bx1, by, bw, bh)
        find_r = pygame.Rect(bx1 + bw + g, by, bw, bh)
        self.renderer.draw_button("Back", back_r, hover=back_r.collidepoint(mouse_pos))
        self.renderer.draw_button("Find Match", find_r, hover=find_r.collidepoint(mouse_pos), active=True)
        rects["back"] = back_r; rects["find_game"] = find_r
        return rects

    # -------------------------------------------------------------------
    # PAUSE MENU
    # -------------------------------------------------------------------
    def draw_pause_menu(self, mouse_pos):
        W, H = self._size()
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 160))
        self.screen.blit(ov, (0, 0))

        pw, ph = 320, 320
        px, py = (W - pw) // 2, (H - ph) // 2
        self.renderer.draw_panel_background(px, py, pw, ph, 240)
        title = self.renderer.fonts['heading'].render("PAUSED", True, COLOR_GOLD)
        self.screen.blit(title, (px + (pw - title.get_width()) // 2, py + 20))

        bw, bh, g = 240, 45, 12
        bx = px + (pw - bw) // 2
        by = py + 70
        buttons = [("Resume","resume"),("Undo Move","undo"),("New Game","new_game"),
                   ("Main Menu","main_menu"),("Quit","quit")]
        rects = {}
        for label, action in buttons:
            r = pygame.Rect(bx, by, bw, bh)
            self.renderer.draw_button(label, r, hover=r.collidepoint(mouse_pos), small=True)
            rects[action] = r; by += bh + g
        return rects

    # -------------------------------------------------------------------
    # GAME HUD BUTTONS
    # -------------------------------------------------------------------
    def draw_game_buttons(self, mouse_pos, y_start, game_mode):
        x = cfg.PANEL_X + 10
        w = cfg.PANEL_WIDTH - 20
        btn_h, gap = 36, 8
        y = y_start
        rects = {}
        buttons = [("Pause","pause"),("New Game","new_game")]
        if game_mode == MODE_VS_PLAYER:
            buttons.insert(1, ("Undo","undo"))
        buttons.append(("Resign","resign"))
        for label, action in buttons:
            r = pygame.Rect(x, y, w, btn_h)
            self.renderer.draw_button(label, r, hover=r.collidepoint(mouse_pos), small=True)
            rects[action] = r; y += btn_h + gap
        return rects

    # -------------------------------------------------------------------
    # ACHIEVEMENTS SCREEN
    # -------------------------------------------------------------------
    def draw_achievements_screen(self, mouse_pos, tracker):
        """Draw the achievements screen with category tabs, grid, and progress."""
        W, H = self._size()
        self.renderer.draw_background()
        rects = {}

        # Title
        title = self.renderer.fonts['heading'].render("ACHIEVEMENTS", True, COLOR_GOLD)
        self.screen.blit(title, ((W - title.get_width()) // 2, 20))

        # Progress bar
        unlocked_count = len(tracker.unlocked)
        total = len(ACHIEVEMENTS)
        prog_text = f"{unlocked_count} / {total} Unlocked"
        pt = self.renderer.fonts['body_small'].render(prog_text, True, COLOR_TEXT_SECONDARY)
        bar_w = min(400, int(W * 0.35))
        bar_x = (W - bar_w) // 2
        bar_y = 52
        self.screen.blit(pt, ((W - pt.get_width()) // 2, bar_y - 2))
        bar_y += 18
        # Bar background
        pygame.draw.rect(self.screen, (40, 40, 50), (bar_x, bar_y, bar_w, 8))
        # Bar fill
        fill_w = int(bar_w * (unlocked_count / max(1, total)))
        if fill_w > 0:
            pygame.draw.rect(self.screen, COLOR_GOLD, (bar_x, bar_y, fill_w, 8))

        # Category tabs
        tab_y = bar_y + 22
        tab_h = 32
        tab_w = min(100, (W - 40) // len(CATEGORIES))
        tab_start_x = (W - tab_w * len(CATEGORIES)) // 2
        for i, cat in enumerate(CATEGORIES):
            tx = tab_start_x + i * tab_w
            r = pygame.Rect(tx, tab_y, tab_w - 4, tab_h)
            active = (cat == self.ach_category)
            self.renderer.draw_button(cat, r, hover=r.collidepoint(mouse_pos),
                                       active=active, small=True)
            rects[f"cat_{cat}"] = r

        # Filter achievements
        all_achs = tracker.get_all_with_status()
        if self.ach_category != "All":
            all_achs = [a for a in all_achs if a["category"] == self.ach_category]

        # Achievement cards grid
        card_w = min(360, int(W * 0.42))
        card_h = 64
        gap = 8
        cols = max(1, (W - 60) // (card_w + gap))
        grid_w = cols * (card_w + gap) - gap
        grid_x = (W - grid_w) // 2
        grid_y = tab_y + tab_h + 16
        max_y = H - 80

        for idx, ach in enumerate(all_achs):
            col_i = idx % cols
            row_i = idx // cols
            cx = grid_x + col_i * (card_w + gap)
            cy = grid_y + row_i * (card_h + gap) - self.ach_scroll

            if cy + card_h < grid_y or cy > max_y:
                continue

            unlocked = ach.get("unlocked", False)
            rarity = ach.get("rarity", "common")
            rc = RARITY_COLORS.get(rarity, (180, 180, 190))

            # Card background
            card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            if unlocked:
                card.fill((28, 32, 38, 230))
            else:
                card.fill((20, 20, 24, 200))
            self.screen.blit(card, (cx, cy))

            # Rarity accent
            accent_color = rc if unlocked else (50, 50, 60)
            pygame.draw.rect(self.screen, accent_color, (cx, cy, 4, card_h))

            # Border
            border_c = rc if unlocked else COLOR_BORDER
            pygame.draw.rect(self.screen, border_c, (cx, cy, card_w, card_h), 1)

            # Icon
            try:
                icon_font = self.renderer.fonts.get('heading')
                icon_text = ach["icon"] if unlocked else "?"
                icon_color = rc if unlocked else (60, 60, 70)
                icon = icon_font.render(icon_text, True, icon_color)
                self.screen.blit(icon, (cx + 12, cy + (card_h - icon.get_height()) // 2))
            except Exception:
                pass

            # Name
            name_color = COLOR_TEXT_PRIMARY if unlocked else (80, 80, 90)
            name = self.renderer.fonts['button_small'].render(ach["name"], True, name_color)
            self.screen.blit(name, (cx + 46, cy + 10))

            # Description
            desc_text = ach["description"] if unlocked else "???"
            desc_color = COLOR_TEXT_SECONDARY if unlocked else (50, 50, 60)
            desc = self.renderer.fonts['body_small'].render(desc_text, True, desc_color)
            self.screen.blit(desc, (cx + 46, cy + 32))

            # Rarity badge (right side)
            if unlocked:
                rb = self.renderer.fonts['body_small'].render(rarity.upper(), True, rc)
                self.screen.blit(rb, (cx + card_w - rb.get_width() - 10, cy + 10))

        # Back button
        bw_btn, bh_btn = 200, 50
        back_r = pygame.Rect((W - bw_btn) // 2, H - 65, bw_btn, bh_btn)
        self.renderer.draw_button("Back", back_r, hover=back_r.collidepoint(mouse_pos))
        rects["back"] = back_r

        return rects

    # -------------------------------------------------------------------
    # ACCOUNT SCREEN
    # -------------------------------------------------------------------
    def draw_account_screen(self, mouse_pos):
        """Draw account login/register/profile screen."""
        W, H = self._size()
        self.renderer.draw_background()
        rects = {}

        title = self.renderer.fonts['heading'].render("ACCOUNT", True, COLOR_GOLD)
        self.screen.blit(title, ((W - title.get_width()) // 2, 30))

        panel_w = min(440, int(W * 0.35))
        panel_h = 380
        px = (W - panel_w) // 2
        py = 80
        self.renderer.draw_panel_background(px, py, panel_w, panel_h, 230)

        btn_w = panel_w - 60
        btn_h = 42
        gap = 10
        ix = px + 30  # inner x

        if self.logged_in and self.account_info:
            # Profile view
            user = self.account_info
            iy = py + 20

            # Username
            un = self.renderer.fonts['button'].render(
                user.get('display_name', user.get('username', '')), True, COLOR_GOLD)
            self.screen.blit(un, (ix, iy)); iy += 40

            # Stats
            stats = [
                f"ELO Rating: {user.get('elo_rating', 1200)}",
                f"Games Played: {user.get('games_played', 0)}",
                f"Games Won: {user.get('games_won', 0)}",
                f"Games Drawn: {user.get('games_drawn', 0)}",
            ]
            for s in stats:
                st = self.renderer.fonts['body'].render(s, True, COLOR_TEXT_PRIMARY)
                self.screen.blit(st, (ix, iy)); iy += 28

            iy += 20
            logout_r = pygame.Rect(ix, iy, btn_w, btn_h)
            self.renderer.draw_button("Logout", logout_r,
                                       hover=logout_r.collidepoint(mouse_pos))
            rects["logout"] = logout_r

        else:
            # Login / Register form
            iy = py + 20

            # Tabs
            half = (btn_w - gap) // 2
            login_tab = pygame.Rect(ix, iy, half, btn_h)
            reg_tab = pygame.Rect(ix + half + gap, iy, half, btn_h)
            self.renderer.draw_button("Login", login_tab,
                hover=login_tab.collidepoint(mouse_pos),
                active=(self.account_mode == 'login'), small=True)
            self.renderer.draw_button("Register", reg_tab,
                hover=reg_tab.collidepoint(mouse_pos),
                active=(self.account_mode == 'register'), small=True)
            rects["tab_login"] = login_tab
            rects["tab_register"] = reg_tab
            iy += btn_h + 20

            # Username field
            self._section("USERNAME", ix, iy); iy += 28
            un_r = pygame.Rect(ix, iy, btn_w, btn_h)
            pygame.draw.rect(self.screen, (35, 35, 45), un_r)
            pygame.draw.rect(self.screen, COLOR_BORDER, un_r, 1)
            un_text = self.renderer.fonts['button_small'].render(
                self.input_username or "...", True,
                COLOR_TEXT_PRIMARY if self.input_username else COLOR_TEXT_DIM)
            self.screen.blit(un_text, (ix + 10, iy + 10))
            rects["field_username"] = un_r
            iy += btn_h + 12

            # Password field
            self._section("PASSWORD", ix, iy); iy += 28
            pw_r = pygame.Rect(ix, iy, btn_w, btn_h)
            pygame.draw.rect(self.screen, (35, 35, 45), pw_r)
            pygame.draw.rect(self.screen, COLOR_BORDER, pw_r, 1)
            pw_display = "*" * len(self.input_password) if self.input_password else "..."
            pw_text = self.renderer.fonts['button_small'].render(
                pw_display, True,
                COLOR_TEXT_PRIMARY if self.input_password else COLOR_TEXT_DIM)
            self.screen.blit(pw_text, (ix + 10, iy + 10))
            rects["field_password"] = pw_r
            iy += btn_h + 16

            # Submit
            action_label = "Login" if self.account_mode == 'login' else "Register"
            submit_r = pygame.Rect(ix, iy, btn_w, btn_h)
            self.renderer.draw_button(action_label, submit_r,
                hover=submit_r.collidepoint(mouse_pos), active=True)
            rects["submit"] = submit_r

            # Error message
            if self.account_error:
                err = self.renderer.fonts['body_small'].render(
                    self.account_error, True, (255, 80, 80))
                self.screen.blit(err, (ix, iy + btn_h + 10))

        # Back button
        back_r = pygame.Rect((W - 200) // 2, H - 65, 200, 50)
        self.renderer.draw_button("Back", back_r, hover=back_r.collidepoint(mouse_pos))
        rects["back"] = back_r

        return rects

        return rects

    # -------------------------------------------------------------------
    # LEARN CHESS
    # -------------------------------------------------------------------
    def draw_learn_menu(self, mouse_pos, tracker):
        """Draw the learn chess chapters and sections."""
        from learn_data import LEARN_CURRICULUM
        W, H = self._size()
        self.renderer.draw_background()

        title = self.renderer.fonts['title'].render("LEARN CHESS", True, COLOR_GOLD)
        self.screen.blit(title, ((W - title.get_width()) // 2, 40))

        # Panel
        pw, ph = int(W * 0.8), int(H * 0.7)
        px, py = (W - pw) // 2, 110
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, (px, py, pw, ph))
        pygame.draw.rect(self.screen, COLOR_BORDER, (px, py, pw, ph), 2)

        rects = {}
        y_offset = py + 20 - self.learn_scroll
        learned = tracker.stats.get("learned_sections", [])

        # Clip area for scrolling
        clip_rect = pygame.Rect(px + 2, py + 2, pw - 4, ph - 4)
        old_clip = self.screen.get_clip()
        self.screen.set_clip(clip_rect)

        for chapter in LEARN_CURRICULUM:
            # Draw Chapter Title
            if py < y_offset + 40 and y_offset < py + ph:
                ctitle = self.renderer.fonts['heading'].render(chapter['title'], True, COLOR_TEXT_PRIMARY)
                self.screen.blit(ctitle, (px + 30, y_offset))
                pygame.draw.line(self.screen, COLOR_BORDER, (px + 30, y_offset + 35), (px + pw - 30, y_offset + 35), 1)
            y_offset += 50

            # Draw Sections
            for section in chapter['sections']:
                is_learned = section['id'] in learned
                color = COLOR_GOLD_BRIGHT if is_learned else COLOR_TEXT_SECONDARY
                icon = "☑" if is_learned else "☐"

                rect = pygame.Rect(px + 40, y_offset, pw - 80, 40)
                if rect.colliderect(clip_rect):
                    hover = rect.collidepoint(mouse_pos)
                    bg = (50, 50, 60) if hover else (40, 40, 50)
                    pygame.draw.rect(self.screen, bg, rect)
                    pygame.draw.rect(self.screen, COLOR_BORDER, rect, 1)

                    text = f"{icon}  {section['title']}"
                    surf = self.renderer.fonts['body'].render(text, True, color)
                    self.screen.blit(surf, (px + 50, y_offset + 8))

                    rects[f"section_{section['id']}"] = rect

                y_offset += 50
            y_offset += 20

        self.screen.set_clip(old_clip)

        # Back button
        back_r = pygame.Rect((W - 200) // 2, H - 65, 200, 50)
        self.renderer.draw_button("Back", back_r, hover=back_r.collidepoint(mouse_pos))
        rects["back"] = back_r

        return rects

    def draw_lesson(self, mouse_pos):
        """Draw a specific lesson reading pane."""
        W, H = self._size()
        self.renderer.draw_background()

        if not self.selected_section:
            return {}

        title_surf = self.renderer.fonts['heading'].render(self.selected_section['title'], True, COLOR_GOLD)
        self.screen.blit(title_surf, ((W - title_surf.get_width()) // 2, 40))

        # Panel
        pw, ph = int(W * 0.8), int(H * 0.7)
        px, py = (W - pw) // 2, 110
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, (px, py, pw, ph))
        pygame.draw.rect(self.screen, COLOR_BORDER, (px, py, pw, ph), 2)

        # Text wrapper
        text = self.selected_section['content']
        self._draw_text_wrapped(self.screen, text, COLOR_TEXT_SECONDARY,
                                pygame.Rect(px + 30, py + 30, pw - 60, ph - 60),
                                self.renderer.fonts['body'])

        rects = {}
        # Back button
        back_r = pygame.Rect(W // 2 - 220, H - 65, 200, 50)
        self.renderer.draw_button("Back", back_r, hover=back_r.collidepoint(mouse_pos))
        rects["back"] = back_r

        # Start Challenge button
        comp_r = pygame.Rect(W // 2 + 20, H - 65, 200, 50)
        self.renderer.draw_button("Start Challenge", comp_r, hover=comp_r.collidepoint(mouse_pos))
        rects["complete"] = comp_r

        return rects



    # -------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------
    def _draw_text_wrapped(self, surface, text, color, rect, font, aa=True):
        """Draw wrapped text inside a rectangle."""
        y = rect.top
        line_spacing = -2
        font_height = font.size("Tg")[1]

        paragraphs = text.split('\n')
        for para in paragraphs:
            if not para:
                y += font_height + line_spacing
                continue

            words = para.split(' ')
            while words:
                i = 1
                while i <= len(words):
                    if font.size(' '.join(words[:i]))[0] > rect.width:
                        break
                    i += 1
                i -= 1
                if i == 0:
                    i = 1
                line = ' '.join(words[:i])
                words = words[i:]
                
                text_surface = font.render(line, aa, color)
                surface.blit(text_surface, (rect.left, y))
                y += font_height + line_spacing

    def _section(self, text, x, y):
        t = self.renderer.fonts['body_small'].render(text, True, COLOR_TEXT_SECONDARY)
        self.screen.blit(t, (x, y))
        pygame.draw.line(self.screen, COLOR_BORDER, (x, y + 20), (x + 120, y + 20), 1)

    def _draw_lesson_overlay(self, instruction):
        """Draw a banner at the top showing the current lesson instruction."""
        W = self._size()[0]
        padding = 15
        
        # Render text
        text_surf = self.renderer.fonts['body'].render(instruction, True, COLOR_TEXT_PRIMARY)
        tw = text_surf.get_width()
        th = text_surf.get_height()
        
        box_w = tw + padding * 4
        box_h = th + padding * 2
        box_x = (W - box_w) // 2
        box_y = 20
        
        # Draw semi-transparent background
        s = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        s.fill((0, 0, 0, 200))
        self.screen.blit(s, (box_x, box_y))
        pygame.draw.rect(self.screen, COLOR_GOLD, (box_x, box_y, box_w, box_h), 2)
        
        self.screen.blit(text_surf, (box_x + padding * 2, box_y + padding))
