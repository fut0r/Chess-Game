"""
achievements.py - Achievement Definitions
25 achievements across 5 categories with condition checkers.
"""

# ---------------------------------------------------------------------------
# Achievement Catalog
# ---------------------------------------------------------------------------
ACHIEVEMENTS = [
    # ---- BEGINNER (5) ----
    {
        "id": "first_move",
        "name": "First Move",
        "description": "Play your first game",
        "icon": "\u265f",
        "category": "Beginner",
        "rarity": "common",
    },
    {
        "id": "first_victory",
        "name": "First Victory",
        "description": "Win your first game",
        "icon": "\u2605",
        "category": "Beginner",
        "rarity": "common",
    },
    {
        "id": "pawn_star",
        "name": "Pawn Star",
        "description": "Promote a pawn for the first time",
        "icon": "\u2654",
        "category": "Beginner",
        "rarity": "common",
    },
    {
        "id": "castle_builder",
        "name": "Castle Builder",
        "description": "Castle for the first time",
        "icon": "\u265c",
        "category": "Beginner",
        "rarity": "common",
    },
    {
        "id": "scholars_mate",
        "name": "Scholar's Mate",
        "description": "Win in 4 moves or fewer",
        "icon": "\u26a1",
        "category": "Beginner",
        "rarity": "rare",
    },
    # ---- COMBAT (5) ----
    {
        "id": "material_hunter",
        "name": "Material Hunter",
        "description": "Capture 50 pieces in total",
        "icon": "\u2694",
        "category": "Combat",
        "rarity": "common",
    },
    {
        "id": "queen_slayer",
        "name": "Queen Slayer",
        "description": "Capture the opponent's queen",
        "icon": "\u2655",
        "category": "Combat",
        "rarity": "common",
    },
    {
        "id": "clean_sweep",
        "name": "Clean Sweep",
        "description": "Win a game without losing any pieces",
        "icon": "\u2728",
        "category": "Combat",
        "rarity": "epic",
    },
    {
        "id": "knight_rider",
        "name": "Knight Rider",
        "description": "Deliver checkmate with a knight",
        "icon": "\u265e",
        "category": "Combat",
        "rarity": "rare",
    },
    {
        "id": "back_rank_mate",
        "name": "Back Rank Mate",
        "description": "Deliver a back rank checkmate",
        "icon": "\u2620",
        "category": "Combat",
        "rarity": "rare",
    },
    # ---- STRATEGY (5) ----
    {
        "id": "endgame_expert",
        "name": "Endgame Expert",
        "description": "Win with only king + pawn vs king",
        "icon": "\u265a",
        "category": "Strategy",
        "rarity": "epic",
    },
    {
        "id": "en_passant_master",
        "name": "En Passant Master",
        "description": "Perform an en passant capture",
        "icon": "\u21a9",
        "category": "Strategy",
        "rarity": "common",
    },
    {
        "id": "double_check",
        "name": "Double Check",
        "description": "Put the opponent's king in double check",
        "icon": "\u2716",
        "category": "Strategy",
        "rarity": "rare",
    },
    {
        "id": "fork_master",
        "name": "Fork Master",
        "description": "Fork the king and queen with a knight",
        "icon": "\u2442",
        "category": "Strategy",
        "rarity": "rare",
    },
    {
        "id": "promotion_army",
        "name": "Promotion Army",
        "description": "Promote 3 pawns in a single game",
        "icon": "\u2657",
        "category": "Strategy",
        "rarity": "epic",
    },
    # ---- MILESTONES (5) ----
    {
        "id": "ten_victories",
        "name": "10 Victories",
        "description": "Win 10 games",
        "icon": "\u2160",
        "category": "Milestones",
        "rarity": "common",
    },
    {
        "id": "fifty_victories",
        "name": "50 Victories",
        "description": "Win 50 games",
        "icon": "\u2174",
        "category": "Milestones",
        "rarity": "rare",
    },
    {
        "id": "hundred_games",
        "name": "100 Games",
        "description": "Play 100 games total",
        "icon": "\u2102",
        "category": "Milestones",
        "rarity": "rare",
    },
    {
        "id": "marathon",
        "name": "Marathon",
        "description": "Play a game lasting 100+ moves",
        "icon": "\u231b",
        "category": "Milestones",
        "rarity": "rare",
    },
    {
        "id": "speed_demon",
        "name": "Speed Demon",
        "description": "Win a Bullet (1+0) game",
        "icon": "\u23f1",
        "category": "Milestones",
        "rarity": "common",
    },
    # ---- MASTERY (5) ----
    {
        "id": "perfect_game",
        "name": "Perfect Game",
        "description": "Win without ever being in check",
        "icon": "\u2b50",
        "category": "Mastery",
        "rarity": "epic",
    },
    {
        "id": "unbreakable",
        "name": "Unbreakable",
        "description": "Win 5 games in a row",
        "icon": "\u26d3",
        "category": "Mastery",
        "rarity": "epic",
    },
    {
        "id": "elo_rising",
        "name": "ELO Rising",
        "description": "Reach 1400 ELO rating",
        "icon": "\u2197",
        "category": "Mastery",
        "rarity": "rare",
    },
    {
        "id": "grandmaster",
        "name": "Grandmaster",
        "description": "Reach 1800 ELO rating",
        "icon": "\u2654",
        "category": "Mastery",
        "rarity": "legendary",
    },
    {
        "id": "completionist",
        "name": "Completionist",
        "description": "Unlock all other achievements",
        "icon": "\u2600",
        "category": "Mastery",
        "rarity": "legendary",
    },
    # ---- LEARN CHESS (3) ----
    {
        "id": "first_lesson",
        "name": "First Lesson",
        "description": "Complete your first learning section",
        "icon": "L",
        "category": "Mastery",
        "rarity": "common",
    },
    {
        "id": "halfway_there",
        "name": "Halfway There",
        "description": "Complete 50% of learning sections",
        "icon": "L",
        "category": "Mastery",
        "rarity": "rare",
    },
    {
        "id": "chess_scholar",
        "name": "Chess Scholar",
        "description": "Complete 100% of learning sections",
        "icon": "L",
        "category": "Mastery",
        "rarity": "epic",
    },
]

# Quick lookup by id
ACHIEVEMENTS_MAP = {a["id"]: a for a in ACHIEVEMENTS}

CATEGORIES = ["All", "Beginner", "Combat", "Strategy", "Milestones", "Mastery"]

RARITY_COLORS = {
    "common": (180, 180, 190),
    "rare": (70, 130, 220),
    "epic": (160, 70, 220),
    "legendary": (240, 170, 40),
}
