"""
notification_manager.py - Toast notification system
Shows achievement unlock popups that slide in from top-right.
"""

import pygame
import time
from achievements import RARITY_COLORS
from config import COLOR_GOLD, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_BORDER


class Notification:
    """A single toast notification."""

    def __init__(self, achievement, start_time):
        self.achievement = achievement
        self.start_time = start_time
        self.duration = 4.0        # total display time (seconds)
        self.slide_in = 0.3        # slide-in duration
        self.slide_out = 0.5       # fade-out duration
        self.width = 320
        self.height = 80

    @property
    def age(self):
        return time.time() - self.start_time

    @property
    def is_expired(self):
        return self.age > self.duration

    @property
    def alpha(self):
        age = self.age
        if age < self.slide_in:
            return int(255 * (age / self.slide_in))
        elif age > self.duration - self.slide_out:
            remaining = self.duration - age
            return int(255 * max(0, remaining / self.slide_out))
        return 255

    @property
    def x_offset(self):
        """Horizontal offset for slide-in animation."""
        age = self.age
        if age < self.slide_in:
            progress = age / self.slide_in
            eased = 1 - (1 - progress) ** 3  # ease-out cubic
            return int(self.width * (1 - eased))
        return 0


class NotificationManager:
    """Manages a queue of toast notifications."""

    def __init__(self):
        self.active = []    # currently showing
        self.queue = []     # waiting to show
        self.max_visible = 3
        self.gap = 10
        self.margin_top = 20
        self.margin_right = 20

    def push(self, achievement):
        """Add an achievement notification to the queue."""
        self.queue.append(achievement)

    def update(self):
        """Update active notifications, promote from queue."""
        # Remove expired
        self.active = [n for n in self.active if not n.is_expired]

        # Add from queue
        while self.queue and len(self.active) < self.max_visible:
            ach = self.queue.pop(0)
            self.active.append(Notification(ach, time.time()))

    def draw(self, screen, fonts):
        """Draw all active notifications."""
        W = screen.get_size()[0]

        for i, notif in enumerate(self.active):
            ach = notif.achievement
            rarity = ach.get("rarity", "common")
            rarity_color = RARITY_COLORS.get(rarity, (180, 180, 190))

            # Position: top-right, stacked
            nw, nh = notif.width, notif.height
            nx = W - nw - self.margin_right + notif.x_offset
            ny = self.margin_top + i * (nh + self.gap)

            # Create surface with alpha
            surf = pygame.Surface((nw, nh), pygame.SRCALPHA)
            alpha = notif.alpha

            # Background
            bg_color = (22, 22, 28, min(240, alpha))
            surf.fill(bg_color)

            # Left accent bar (rarity color)
            accent_surf = pygame.Surface((4, nh), pygame.SRCALPHA)
            accent_surf.fill((*rarity_color, alpha))
            surf.blit(accent_surf, (0, 0))

            # Border
            border_surf = pygame.Surface((nw, nh), pygame.SRCALPHA)
            pygame.draw.rect(border_surf, (*COLOR_BORDER, alpha), (0, 0, nw, nh), 1)
            surf.blit(border_surf, (0, 0))

            # "ACHIEVEMENT UNLOCKED" header
            header_font = fonts.get('body_small', pygame.font.SysFont('Arial', 12))
            header = header_font.render("ACHIEVEMENT UNLOCKED", True, (*COLOR_GOLD[:3],))
            header.set_alpha(alpha)
            surf.blit(header, (14, 8))

            # Achievement name
            name_font = fonts.get('button_small', pygame.font.SysFont('Arial', 16))
            name = name_font.render(ach["name"], True, COLOR_TEXT_PRIMARY)
            name.set_alpha(alpha)
            surf.blit(name, (14, 28))

            # Description
            desc_font = fonts.get('body_small', pygame.font.SysFont('Arial', 12))
            desc = desc_font.render(ach["description"], True, COLOR_TEXT_SECONDARY)
            desc.set_alpha(alpha)
            surf.blit(desc, (14, 50))

            # Icon (right side)
            try:
                icon_font = fonts.get('timer', pygame.font.SysFont('Segoe UI Emoji', 28))
                icon = icon_font.render(ach.get("icon", "?"), True, rarity_color)
                icon.set_alpha(alpha)
                surf.blit(icon, (nw - 50, (nh - icon.get_height()) // 2))
            except Exception:
                pass

            screen.blit(surf, (nx, ny))
