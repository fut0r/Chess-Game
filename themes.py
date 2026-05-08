"""
themes.py - Board and UI Theme Definitions
"""

from config import BOARD_THEMES, DEFAULT_THEME


class ThemeManager:
    """Manages board themes and provides color getters."""

    def __init__(self):
        self.current_theme_name = DEFAULT_THEME
        self.themes = BOARD_THEMES

    def get_theme(self):
        """Get the current theme colors."""
        return self.themes[self.current_theme_name]

    def get_light_color(self):
        return self.themes[self.current_theme_name]["light"]

    def get_dark_color(self):
        return self.themes[self.current_theme_name]["dark"]

    def get_border_color(self):
        return self.themes[self.current_theme_name]["border"]

    def set_theme(self, name):
        """Switch to a different theme."""
        if name in self.themes:
            self.current_theme_name = name

    def get_theme_names(self):
        """Get list of available theme names."""
        return list(self.themes.keys())

    def next_theme(self):
        """Cycle to the next theme."""
        names = self.get_theme_names()
        idx = names.index(self.current_theme_name)
        self.current_theme_name = names[(idx + 1) % len(names)]
        return self.current_theme_name
