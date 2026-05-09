"""
renderer.py - Pygame Rendering Engine
All layout values read dynamically from config module so they update
when resolution changes. All corners sharp/boxed.
"""

import pygame
import os
import time
import config as cfg
from config import (
    BOARD_SIZE, AI_MOVE_ANIMATION_MS,
    COLOR_BG_DARK, COLOR_BG_MEDIUM, COLOR_OVERLAY, COLOR_OVERLAY_LIGHT,
    COLOR_GOLD, COLOR_GOLD_DIM, COLOR_GOLD_BRIGHT, COLOR_AMBER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_DIM,
    COLOR_CHECK, COLOR_LAST_MOVE, COLOR_SELECTED, COLOR_LEGAL_MOVE, COLOR_LEGAL_CAPTURE,
    COLOR_BUTTON, COLOR_BUTTON_HOVER, COLOR_BUTTON_ACTIVE, COLOR_PANEL_BG, COLOR_BORDER,
    COLOR_TIMER_NORMAL, COLOR_TIMER_WARNING, COLOR_TIMER_CRITICAL,
    PIECES_DIR, FONT_ULTRALIGHT, FONT_MEDIUM, FONT_BOLD, FONT_CARVIST,
    BACKGROUND_IMAGE, FILES, RANKS,
)
from utils import board_to_pixel, get_piece_image_name, is_white_piece


class MoveAnimation:
    """Handles smooth piece animation for AI moves."""

    def __init__(self):
        self.active = False
        self.piece = None
        self.from_pixel = (0, 0)
        self.to_pixel = (0, 0)
        self.from_sq = None
        self.to_sq = None
        self.start_time = 0
        self.duration_ms = AI_MOVE_ANIMATION_MS
        self.progress = 0.0
        self.progress_eased = 0.0

    def start(self, piece, from_sq, to_sq, flipped=False):
        """Start animating a piece from one square to another."""
        self.active = True
        self.piece = piece
        self.from_sq = from_sq
        self.to_sq = to_sq
        fx, fy = board_to_pixel(*from_sq, flipped=flipped)
        tx, ty = board_to_pixel(*to_sq, flipped=flipped)
        self.from_pixel = (fx, fy)
        self.to_pixel = (tx, ty)
        self.start_time = time.time()
        self.progress = 0.0
        self.progress_eased = 0.0

    def update(self):
        """Update animation progress. Returns True if still animating."""
        if not self.active:
            return False
        elapsed = (time.time() - self.start_time) * 1000
        self.progress = min(1.0, elapsed / self.duration_ms)
        t = self.progress
        # Quartic Ease-Out for a premium, snappy glide
        self.progress_eased = 1.0 - (1.0 - t) ** 4
        if self.progress >= 1.0:
            self.active = False
            return False
        return True

    def get_current_pos(self):
        """Get current interpolated pixel position."""
        t = self.progress_eased
        x = self.from_pixel[0] + (self.to_pixel[0] - self.from_pixel[0]) * t
        y = self.from_pixel[1] + (self.to_pixel[1] - self.from_pixel[1]) * t
        return (int(x), int(y))

    @property
    def from_sq_board(self):
        """Get the from square in board coords."""
        return self.from_sq

    @property
    def to_sq_board(self):
        """Get the to square in board coords."""
        return self.to_sq


class Renderer:
    """Handles all visual rendering for the chess game."""

    def __init__(self, screen):
        self.screen = screen
        self.piece_images = {}
        self.piece_images_raw = {}  # original full-size for re-scaling
        self.fonts = {}
        self.background_raw = None  # original loaded background
        self.background = None      # scaled to current window
        self.animation = MoveAnimation()
        self._load_fonts()
        self._load_pieces()
        self._load_background()
        
    def resize(self, new_screen):
        """Handle resolution change: update screen, re-scale assets."""
        self.screen = new_screen
        self._scale_background()
        self._scale_pieces()
        self._load_fonts()
    def _load_fonts(self):
        """Load all fonts."""
        try:
            self.fonts['title'] = pygame.font.Font(FONT_ULTRALIGHT, 52)
            self.fonts['subtitle'] = pygame.font.Font(FONT_ULTRALIGHT, 28)
            self.fonts['heading'] = pygame.font.Font(FONT_BOLD, 24)
            self.fonts['body'] = pygame.font.Font(FONT_MEDIUM, 18)
            self.fonts['body_small'] = pygame.font.Font(FONT_MEDIUM, 14)
            self.fonts['button'] = pygame.font.Font(FONT_MEDIUM, 20)
            self.fonts['button_small'] = pygame.font.Font(FONT_MEDIUM, 16)
            self.fonts['timer'] = pygame.font.Font(FONT_BOLD, 32)
            self.fonts['timer_small'] = pygame.font.Font(FONT_BOLD, 22)
            self.fonts['coord'] = pygame.font.Font(FONT_MEDIUM, 13)
            self.fonts['splash_title'] = pygame.font.Font(FONT_ULTRALIGHT, 72)
            self.fonts['splash_sub'] = pygame.font.Font(FONT_ULTRALIGHT, 24)
            self.fonts['move_notation'] = pygame.font.Font(FONT_MEDIUM, 15)
            self.fonts['piece_symbol'] = pygame.font.Font(FONT_BOLD, 16)
            self.fonts['game_over'] = pygame.font.Font(FONT_BOLD, 42)
            self.fonts['game_over_sub'] = pygame.font.Font(FONT_ULTRALIGHT, 26)
            self.fonts['slang'] = pygame.font.Font(FONT_CARVIST, 32)
        except Exception:
            # Fallback if font loading fails
            pass
            for key in ['title', 'subtitle', 'heading', 'body', 'body_small',
                         'button', 'button_small', 'timer', 'timer_small',
                         'coord', 'splash_title', 'splash_sub', 'move_notation',
                         'piece_symbol', 'game_over', 'game_over_sub']:
                self.fonts[key] = pygame.font.SysFont('Arial', 20)

    def _load_pieces(self):
        """Load raw piece images from disk and trim them."""
        piece_chars = ['K', 'Q', 'R', 'B', 'N', 'P', 'k', 'q', 'r', 'b', 'n', 'p']
        for pc in piece_chars:
            img_name = get_piece_image_name(pc)
            if img_name:
                path = os.path.join(PIECES_DIR, img_name)
                if os.path.exists(path):
                    try:
                        img = pygame.image.load(path).convert_alpha()
                        # Smart-trim transparency to ensure perfect centering
                        img = self._trim_transparency(img)
                        self.piece_images_raw[pc] = img
                    except Exception:
                        continue
        self._scale_pieces()

    def _trim_transparency(self, surface):
        """Helper to trim transparent borders from a surface."""
        mask = pygame.mask.from_surface(surface)
        rects = mask.get_bounding_rects()
        if not rects: return surface
        # Find the bounding box of all non-transparent pixels
        min_x, min_y = surface.get_width(), surface.get_height()
        max_x, max_y = 0, 0
        for r in rects:
            min_x = min(min_x, r.x); min_y = min(min_y, r.y)
            max_x = max(max_x, r.x + r.width); max_y = max(max_y, r.y + r.height)
        
        trimmed = pygame.Surface((max_x - min_x, max_y - min_y), pygame.SRCALPHA)
        trimmed.blit(surface, (0, 0), (min_x, min_y, max_x - min_x, max_y - min_y))
        return trimmed

    def _scale_pieces(self):
        """Scale pieces to fit SQUARE_SIZE while maintaining aspect ratio."""
        target_h = int(cfg.SQUARE_SIZE * 0.88)
        for pc, raw in self.piece_images_raw.items():
            rw, rh = raw.get_size()
            ratio = target_h / rh
            new_w = int(rw * ratio)
            self.piece_images[pc] = pygame.transform.smoothscale(raw, (new_w, target_h))

    def _load_background(self):
        """Load the raw background image."""
        if os.path.exists(BACKGROUND_IMAGE):
            self.background_raw = pygame.image.load(BACKGROUND_IMAGE).convert()
        self._scale_background()

    def _scale_background(self):
        """Scale background to current window size."""
        if self.background_raw:
            w, h = self.screen.get_size()
            self.background = pygame.transform.smoothscale(self.background_raw, (w, h))
        else:
            self.background = None

    def draw_background(self):
        """Draw the background image with dark overlay."""
        w, h = self.screen.get_size()
        if self.background:
            self.screen.blit(self.background, (0, 0))
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
        else:
            self.screen.fill(COLOR_BG_DARK)

    def draw_board(self, theme_manager, selected=None, legal_moves=None,
                   last_move=None, check_square=None, show_coordinates=True, flipped=False):
        """Draw the chess board with highlights."""
        SQ = cfg.SQUARE_SIZE
        BX = cfg.BOARD_OFFSET_X
        BY = cfg.BOARD_OFFSET_Y
        BPX = cfg.BOARD_PIXEL_SIZE

        light = theme_manager.get_light_color()
        dark = theme_manager.get_dark_color()
        border_color = theme_manager.get_border_color()

        # Board border
        bw = 4
        frame = pygame.Rect(BX - bw - 2, BY - bw - 2,
                             BPX + bw * 2 + 4, BPX + bw * 2 + 4)
        pygame.draw.rect(self.screen, border_color, frame, bw)

        # Squares
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                x, y = board_to_pixel(col, row, flipped=flipped)
                color = light if (row + col) % 2 == 0 else dark
                pygame.draw.rect(self.screen, color, (x, y, SQ, SQ))

        # Last move
        if last_move:
            ov = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
            ov.fill(COLOR_LAST_MOVE)
            for sq in (last_move.from_sq, last_move.to_sq):
                self.screen.blit(ov, board_to_pixel(*sq, flipped=flipped))

        # Selected
        if selected:
            ov = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
            ov.fill(COLOR_SELECTED)
            self.screen.blit(ov, board_to_pixel(*selected, flipped=flipped))

        # Legal moves
        if legal_moves:
            for move in legal_moves:
                x, y = board_to_pixel(*move.to_sq, flipped=flipped)
                ov = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
                if move.captured or move.is_en_passant:
                    ov.fill(COLOR_LEGAL_CAPTURE)
                else:
                    pygame.draw.circle(ov, (*COLOR_LEGAL_MOVE[:3], 140),
                                       (SQ // 2, SQ // 2), SQ // 6)
                self.screen.blit(ov, (x, y))

        # Check
        if check_square:
            ov = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
            ov.fill(COLOR_CHECK)
            self.screen.blit(ov, board_to_pixel(*check_square, flipped=flipped))

        # Coordinates
        if show_coordinates:
            for i in range(BOARD_SIZE):
                # Files (A-H)
                file_text = FILES[7-i] if flipped else FILES[i]
                text = self.fonts['coord'].render(file_text, True, COLOR_TEXT_DIM)
                tx = BX + i * SQ + SQ // 2 - text.get_width() // 2
                self.screen.blit(text, (tx, BY + BPX + 6))

                # Ranks (1-8)
                rank_text = RANKS[7-i] if flipped else RANKS[i]
                text = self.fonts['coord'].render(rank_text, True, COLOR_TEXT_DIM)
                tx = BX - text.get_width() - 8
                ty = BY + i * SQ + SQ // 2 - text.get_height() // 2
                self.screen.blit(text, (tx, ty))

    def draw_pieces(self, board, dragging_piece=None, drag_pos=None, drag_from=None, flipped=False):
        """Draw all pieces on the board."""
        SQ = cfg.SQUARE_SIZE
        anim_from = self.animation.from_sq_board if self.animation.active else None

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = board[row][col]
                if piece == '.':
                    continue
                if drag_from and (col, row) == drag_from:
                    continue
                if anim_from and (col, row) == anim_from:
                    continue
                # Also hide the target square during animation to avoid "ghosting",
                # as make_move is called before the animation finishes.
                anim_to = self.animation.to_sq_board if self.animation.active else None
                if anim_to and (col, row) == anim_to:
                    continue
                if piece in self.piece_images:
                    img = self.piece_images[piece]
                    x, y = board_to_pixel(col, row, flipped=flipped)
                    px = x + (SQ - img.get_width()) // 2
                    py = y + (SQ - img.get_height()) // 2
                    self.screen.blit(img, (px, py))

        # Animated piece
        if self.animation.active and self.animation.piece in self.piece_images:
            self.animation.update()
            img = self.piece_images[self.animation.piece]
            ax, ay = self.animation.get_current_pos()
            self.screen.blit(img, (ax + (SQ - img.get_width()) // 2,
                                    ay + (SQ - img.get_height()) // 2))

        # Dragged piece
        if dragging_piece and drag_pos and dragging_piece in self.piece_images:
            img = self.piece_images[dragging_piece]
            self.screen.blit(img, (drag_pos[0] - img.get_width() // 2,
                                    drag_pos[1] - img.get_height() // 2))

    def draw_panel_background(self, x, y, w, h, alpha=220):
        """Draw a semi-transparent panel background."""
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill((22, 22, 28, alpha))
        self.screen.blit(panel, (x, y))
        pygame.draw.rect(self.screen, COLOR_BORDER, (x, y, w, h), 1)

    def draw_clocks(self, clock, y_offset=0, white_name="WHITE", black_name="BLACK"):
        """Draw the chess clocks on the side panel."""
        clock_width = cfg.PANEL_WIDTH - 20
        clock_height = 60
        x = cfg.PANEL_X + 10

        by = cfg.PANEL_Y + y_offset
        self.draw_panel_background(x, by, clock_width, clock_height)
        if clock.is_black_active():
            pygame.draw.rect(self.screen, COLOR_GOLD, (x, by, 3, clock_height))
        
        # Truncate names if too long
        b_label = str(black_name).upper()[:16]
        self.screen.blit(self.fonts['body_small'].render(b_label, True, COLOR_TEXT_SECONDARY),
                         (x + 12, by + 8))
        state = clock.get_black_state()
        tc = COLOR_TIMER_CRITICAL if state == 'critical' else COLOR_TIMER_WARNING if state == 'warning' else COLOR_TIMER_NORMAL
        self.screen.blit(self.fonts['timer'].render(clock.get_black_display(), True, tc),
                         (x + 12, by + 24))

        wy = by + clock_height + 8
        self.draw_panel_background(x, wy, clock_width, clock_height)
        if clock.is_white_active():
            pygame.draw.rect(self.screen, COLOR_GOLD, (x, wy, 3, clock_height))
        
        w_label = str(white_name).upper()[:16]
        self.screen.blit(self.fonts['body_small'].render(w_label, True, COLOR_TEXT_SECONDARY),
                         (x + 12, wy + 8))
        state = clock.get_white_state()
        tc = COLOR_TIMER_CRITICAL if state == 'critical' else COLOR_TIMER_WARNING if state == 'warning' else COLOR_TIMER_NORMAL
        self.screen.blit(self.fonts['timer'].render(clock.get_white_display(), True, tc),
                         (x + 12, wy + 24))

        return wy + clock_height + 12

    def draw_captured_pieces(self, engine, y_start):
        """Draw captured pieces display."""
        x = cfg.PANEL_X + 10
        w = cfg.PANEL_WIDTH - 20
        h = 70
        self.draw_panel_background(x, y_start, w, h)
        self.screen.blit(self.fonts['body_small'].render("CAPTURED", True, COLOR_TEXT_SECONDARY),
                         (x + 12, y_start + 6))

        ps = 22
        cx = x + 12
        for i, p in enumerate(sorted(engine.white_captured,
                key=lambda c: {'p':1,'n':3,'b':3,'r':5,'q':9}.get(c.lower(),0), reverse=True)):
            if p in self.piece_images:
                img = pygame.transform.smoothscale(self.piece_images[p], (ps, ps))
                self.screen.blit(img, (cx + i * (ps - 2), y_start + 24))
        for i, p in enumerate(sorted(engine.black_captured,
                key=lambda c: {'p':1,'n':3,'b':3,'r':5,'q':9}.get(c.lower(),0), reverse=True)):
            if p in self.piece_images:
                img = pygame.transform.smoothscale(self.piece_images[p], (ps, ps))
                self.screen.blit(img, (cx + i * (ps - 2), y_start + 48))

        return y_start + h + 8

    def draw_move_history(self, engine, y_start, max_height=280):
        """Draw move history panel."""
        x = cfg.PANEL_X + 10
        w = cfg.PANEL_WIDTH - 20
        self.draw_panel_background(x, y_start, w, max_height)
        self.screen.blit(self.fonts['body_small'].render("MOVES", True, COLOR_TEXT_SECONDARY),
                         (x + 12, y_start + 6))
        moves = engine.get_move_list_display()
        lh = 20
        vis = (max_height - 30) // lh
        start = max(0, len(moves) - vis)
        for i, line in enumerate(moves[start:]):
            ty = y_start + 28 + i * lh
            if ty + lh > y_start + max_height:
                break
            color = COLOR_TEXT_PRIMARY if i + start == len(moves) - 1 else COLOR_TEXT_SECONDARY
            self.screen.blit(self.fonts['move_notation'].render(line, True, color), (x + 12, ty))
        return y_start + max_height + 8

    def draw_status_bar(self, engine, game_mode, y_pos):
        """Draw game status."""
        x = cfg.PANEL_X + 10
        if engine.game_over:
            if engine.is_checkmate:
                s = f"Checkmate! {engine.winner.title()} wins"
            elif engine.is_draw:
                s = f"Draw - {engine.draw_reason}"
            else:
                s = f"{engine.winner.title()} wins"
            c = COLOR_GOLD
        elif engine.is_check:
            who = "White" if engine.white_turn else "Black"
            s, c = f"{who} is in CHECK!", COLOR_TIMER_CRITICAL
        else:
            who = "White" if engine.white_turn else "Black"
            s, c = f"{who} to move", COLOR_TEXT_PRIMARY
        self.screen.blit(self.fonts['body'].render(s, True, c), (x, y_pos))

    def draw_button(self, text, rect, hover=False, active=False, small=False):
        """Draw a styled button &#8212; sharp corners."""
        color = COLOR_BUTTON_ACTIVE if active else (COLOR_BUTTON_HOVER if hover else COLOR_BUTTON)
        text_color = COLOR_BG_DARK if active else COLOR_TEXT_PRIMARY
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, COLOR_BORDER, rect, 1)
        fk = 'button_small' if small else 'button'
        label = self.fonts[fk].render(text, True, text_color)
        self.screen.blit(label, (rect.x + (rect.width - label.get_width()) // 2,
                                  rect.y + (rect.height - label.get_height()) // 2))
        return rect

    def draw_promotion_dialog(self, is_white):
        """Draw pawn promotion selection dialog."""
        W, H = self.screen.get_size()
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 160))
        self.screen.blit(ov, (0, 0))

        dw, dh = 360, 160
        dx, dy = (W - dw) // 2, (H - dh) // 2
        self.draw_panel_background(dx, dy, dw, dh, 240)
        title = self.fonts['heading'].render("Promote Pawn", True, COLOR_GOLD)
        self.screen.blit(title, (dx + (dw - title.get_width()) // 2, dy + 12))

        pieces = ['Q','R','B','N'] if is_white else ['q','r','b','n']
        ps, sp = 60, 16
        tw = len(pieces) * ps + (len(pieces) - 1) * sp
        sx, py = dx + (dw - tw) // 2, dy + 55
        options = []
        mp = pygame.mouse.get_pos()
        for i, pc in enumerate(pieces):
            px = sx + i * (ps + sp)
            r = pygame.Rect(px, py, ps, ps)
            hv = r.collidepoint(mp)
            pygame.draw.rect(self.screen, COLOR_BUTTON_HOVER if hv else COLOR_BUTTON, r)
            pygame.draw.rect(self.screen, COLOR_GOLD if hv else COLOR_BORDER, r, 2)
            if pc in self.piece_images:
                img = pygame.transform.smoothscale(self.piece_images[pc], (ps-12, ps-12))
                self.screen.blit(img, (px+6, py+6))
            options.append((r, pc))
        return options

    def draw_game_over_overlay(self, engine):
        """Draw game over screen overlay."""
        W, H = self.screen.get_size()
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 180))
        self.screen.blit(ov, (0, 0))

        if engine.is_checkmate:
            res, sub = "CHECKMATE", f"{engine.winner.title()} wins!"
        elif engine.is_draw:
            res, sub = "DRAW", engine.draw_reason
        else:
            res = "GAME OVER"
            sub = f"{engine.winner.title()} wins!" if engine.winner else ""

        rt = self.fonts['game_over'].render(res, True, COLOR_GOLD)
        ry = H // 2 - 80
        self.screen.blit(rt, ((W - rt.get_width()) // 2, ry))
        if sub:
            st = self.fonts['game_over_sub'].render(sub, True, COLOR_TEXT_PRIMARY)
            self.screen.blit(st, ((W - st.get_width()) // 2, ry + 55))

        bw, bh, gap = 180, 45, 20
        total = bw * 2 + gap
        bx1 = (W - total) // 2
        by = ry + 120
        mp = pygame.mouse.get_pos()
        pr = pygame.Rect(bx1, by, bw, bh)
        mr = pygame.Rect(bx1 + bw + gap, by, bw, bh)
        self.draw_button("Play Again", pr, hover=pr.collidepoint(mp))
        self.draw_button("Main Menu", mr, hover=mr.collidepoint(mp))
        return pr, mr
    def draw_rotated_text(self, text, font_key, size, color, center, angle):
        """Draw rotated text centered at a position."""
        font = self.fonts.get(font_key, self.fonts['medium']).get(size, self.fonts['medium'][24])
        # Render lowercase as requested
        text_surf = font.render(text.lower(), True, color)
        rotated_surf = pygame.transform.rotate(text_surf, angle)
        rect = rotated_surf.get_rect(center=center)
        self.screen.blit(rotated_surf, rect)
