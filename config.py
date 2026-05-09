"""
config.py - Central configuration for the Chess Game
All constants, paths, colors, timing presets, and game settings.
"""

import os
import sys

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
if sys.platform == 'emscripten':
    RESOURCE_DIR = "."
    DATA_DIR = "."
elif getattr(sys, 'frozen', False):
    RESOURCE_DIR = sys._MEIPASS
    DATA_DIR = os.path.dirname(sys.executable)
else:
    RESOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = RESOURCE_DIR

ASSETS_DIR = os.path.join(RESOURCE_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
PIECES_DIR = os.path.join(ASSETS_DIR, "pieces")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")

FONT_ULTRALIGHT = os.path.join(FONTS_DIR, "HelveticaNeueUltraLight.otf")
FONT_MEDIUM = os.path.join(FONTS_DIR, "HelveticaNeueMedium.otf")
FONT_BOLD = os.path.join(FONTS_DIR, "HelveticaNeueBold.otf")
FONT_CARVIST = os.path.join(FONTS_DIR, "TT Carvist Trial Bold.ttf")
BACKGROUND_IMAGE = os.path.join(ASSETS_DIR, "background-game.jpg")

# ---------------------------------------------------------------------------
# Window
# ---------------------------------------------------------------------------
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
FPS = 60
GAME_TITLE = "Chess Game"
GAME_VERSION = "0.3"
GAME_AUTHOR = "fut0r (Zyad Mohamed)"

# ---------------------------------------------------------------------------
# Board Layout (computed &#8212; call recalculate_layout() after resolution change)
# ---------------------------------------------------------------------------
BOARD_SIZE = 8
SQUARE_SIZE = 80
BOARD_PIXEL_SIZE = BOARD_SIZE * SQUARE_SIZE  # 640
BOARD_OFFSET_X = 60
BOARD_OFFSET_Y = 80
COORD_MARGIN = 25

# Side panel (right of board)
PANEL_X = BOARD_OFFSET_X + BOARD_PIXEL_SIZE + 40
PANEL_WIDTH = WINDOW_WIDTH - PANEL_X - 20
PANEL_Y = BOARD_OFFSET_Y


def recalculate_layout(width, height):
    """Recalculate all layout globals for a new window size."""
    global WINDOW_WIDTH, WINDOW_HEIGHT, SQUARE_SIZE, BOARD_PIXEL_SIZE
    global BOARD_OFFSET_X, BOARD_OFFSET_Y, PANEL_X, PANEL_WIDTH, PANEL_Y

    WINDOW_WIDTH = width
    WINDOW_HEIGHT = height

    # Scale square size to fit board in window height with padding
    SQUARE_SIZE = max(50, min(100, (height - 160) // BOARD_SIZE))
    BOARD_PIXEL_SIZE = BOARD_SIZE * SQUARE_SIZE

    # Position board with left margin proportional to window width
    BOARD_OFFSET_X = max(40, int(width * 0.05))
    BOARD_OFFSET_Y = (height - BOARD_PIXEL_SIZE) // 2

    # Side panel fills remaining space
    PANEL_X = BOARD_OFFSET_X + BOARD_PIXEL_SIZE + int(width * 0.03)
    PANEL_WIDTH = width - PANEL_X - 20
    PANEL_Y = BOARD_OFFSET_Y



# ---------------------------------------------------------------------------
# Colors &#8212; Premium palette
# ---------------------------------------------------------------------------
# Background & Overlay
COLOR_BG_DARK = (18, 18, 22)
COLOR_BG_MEDIUM = (28, 28, 35)
COLOR_OVERLAY = (0, 0, 0, 180)
COLOR_OVERLAY_LIGHT = (0, 0, 0, 120)

# Accent colors
COLOR_GOLD = (212, 168, 67)
COLOR_GOLD_DIM = (160, 128, 50)
COLOR_GOLD_BRIGHT = (240, 200, 90)
COLOR_SILVER = (192, 192, 192)
COLOR_BRONZE = (205, 127, 50)
COLOR_AMBER = (255, 191, 0)

# Text
COLOR_TEXT_PRIMARY = (240, 240, 245)
COLOR_TEXT_SECONDARY = (160, 160, 170)
COLOR_TEXT_DIM = (100, 100, 110)

# Game state
COLOR_CHECK = (220, 50, 50, 100)
COLOR_LAST_MOVE = (170, 162, 58, 90)
COLOR_SELECTED = (106, 135, 77, 150)
COLOR_LEGAL_MOVE = (106, 135, 77, 100)
COLOR_LEGAL_CAPTURE = (200, 70, 70, 120)

# UI Elements
COLOR_BUTTON = (45, 45, 55)
COLOR_BUTTON_HOVER = (60, 60, 75)
COLOR_BUTTON_ACTIVE = (212, 168, 67)
COLOR_PANEL_BG = (22, 22, 28, 220)
COLOR_BORDER = (60, 60, 70)

# Timer warnings
COLOR_TIMER_NORMAL = (240, 240, 245)
COLOR_TIMER_WARNING = (255, 200, 50)
COLOR_TIMER_CRITICAL = (255, 70, 70)

# ---------------------------------------------------------------------------
# Board Themes
# ---------------------------------------------------------------------------
BOARD_THEMES = {
    "Classic": {
        "light": (240, 217, 181),
        "dark": (181, 136, 99),
        "name": "Classic",
        "border": (120, 90, 60),
    },
    "Modern Dark": {
        "light": (100, 100, 105),
        "dark": (50, 50, 55),
        "name": "Modern Dark",
        "border": (35, 35, 40),
    },
    "Marble": {
        "light": (232, 224, 212),
        "dark": (139, 125, 107),
        "name": "Marble",
        "border": (100, 85, 70),
    },
    "Wood": {
        "light": (222, 184, 135),
        "dark": (139, 105, 20),
        "name": "Wood",
        "border": (90, 65, 10),
    },
}

DEFAULT_THEME = "Classic"

# ---------------------------------------------------------------------------
# Time Controls
# ---------------------------------------------------------------------------
TIME_CONTROLS = {
    "Bullet 1+0": {"time": 60, "increment": 0},
    "Blitz 3+0": {"time": 180, "increment": 0},
    "Blitz 5+0": {"time": 300, "increment": 0},
    "Rapid 10+0": {"time": 600, "increment": 0},
    "Rapid 15+10": {"time": 900, "increment": 10},
    "Classical 30+0": {"time": 1800, "increment": 0},
    "Endless": {"time": 0, "increment": 0},
}

DEFAULT_TIME_CONTROL = "Blitz 5+0"

# ---------------------------------------------------------------------------
# AI Settings
# ---------------------------------------------------------------------------
AI_DIFFICULTIES = {
    "Easy": {"depth": 1, "noise": 0.3},
    "Medium": {"depth": 2, "noise": 0.1},
    "Hard": {"depth": 3, "noise": 0.0},
    "Expert": {"depth": 4, "noise": 0.0},
}

# Piece values for evaluation
PIECE_VALUES = {
    'P': 100,  'N': 320,  'B': 330,  'R': 500,  'Q': 900,  'K': 20000,
    'p': -100, 'n': -320, 'b': -330, 'r': -500, 'q': -900, 'k': -20000,
}

# ---------------------------------------------------------------------------
# Game Modes
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Piece Characters (internal representation)
# ---------------------------------------------------------------------------
# Uppercase = White, lowercase = Black
# K=King, Q=Queen, R=Rook, B=Bishop, N=Knight, P=Pawn
# '.' = empty square

INITIAL_BOARD = [
    ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
    ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
    ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R'],
]

# File and Rank labels
FILES = "abcdefgh"
RANKS = "87654321"

# ---------------------------------------------------------------------------
# Animation & UI
# ---------------------------------------------------------------------------
ANIMATION_SPEED = 12  # pixels per frame for piece movement
FADE_SPEED = 8  # alpha change per frame for transitions
SPLASH_DURATION = 3000  # milliseconds
AI_MOVE_ANIMATION_MS = 450  # duration of AI move slide animation (slower = more premium)

# ---------------------------------------------------------------------------
# Resolution & Display
# ---------------------------------------------------------------------------
RESOLUTIONS = {
    "1280x800": (1280, 800),
    "1366x768": (1366, 768),
    "1600x900": (1600, 900),
    "1920x1080": (1920, 1080),
}
DISPLAY_MODES = ["Windowed", "Fullscreen", "Borderless"]
DEFAULT_RESOLUTION = "1280x800"
DEFAULT_DISPLAY_MODE = "Windowed"

# ---------------------------------------------------------------------------
# Online Multiplayer
# ---------------------------------------------------------------------------
MODE_VS_AI = "vs_ai"
MODE_VS_PLAYER = "vs_player"
MODE_ONLINE = "online"
MODE_LESSON = "lesson"

GAME_MODES = [
    {"id": MODE_VS_AI, "name": "vs AI", "desc": "Play against the computer engine"},
    {"id": MODE_VS_PLAYER, "name": "Local Multiplayer", "desc": "Play with a friend on this device"},
    {"id": MODE_ONLINE, "name": "Play Online", "desc": "Play with opponents worldwide (Beta)"},
    {"id": MODE_LESSON, "name": "Learn Chess", "desc": "Masterclass interactive puzzles"},
]

VARIANTS = ["Standard", "Chess960"]

SERVERS = {
    "Frankfurt": {"host": "18.196.205.59", "port": 8765, "flag": "DE"},
    "Local": {"host": "localhost", "port": 8765, "flag": "SA"},
}

DEFAULT_SERVER = "Frankfurt"

# ---------------------------------------------------------------------------
# Backend API
# ---------------------------------------------------------------------------
BACKEND_API_URL = "http://18.196.205.59:8000"
