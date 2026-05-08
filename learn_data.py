"""
learn_data.py - Data structure for the Learn Chess module.
Contains chapters, sections, and lesson content with interactive challenges.
"""

LEARN_CURRICULUM = [
    {
        "id": "chapter_1",
        "title": "Chapter 1: The Battlefield Basics",
        "sections": [
            {
                "id": "c1_s1",
                "title": "The Board & Coordinates",
                "content": (
                    "Welcome to the Masterclass. Let's start with the battlefield itself.\n\n"
                    "The chessboard is a 64-square grid. The squares alternate between light and dark colors. "
                    "Always remember the golden rule when setting up the board: 'White on right'. "
                    "This means the bottom-right square for each player MUST be a light square.\n\n"
                    "We use a coordinate system to map the board. The vertical columns are called 'files' (labeled 'a' through 'h'). "
                    "The horizontal rows are called 'ranks' (numbered '1' through '8'). Every square has a unique name, like 'e4' or 'g7'."
                ),
                "challenge_fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                "expected_moves": [],
                "instruction": "Just click Start Challenge to complete this lesson!"
            },
            {
                "id": "c1_s2",
                "title": "The Pieces & Their Value",
                "content": (
                    "To win wars, you need to know the value of your troops. Here is the standard point system used by Grandmasters:\n\n"
                    "- Pawn: 1 point\n"
                    "- Knight: 3 points\n"
                    "- Bishop: 3 points\n"
                    "- Rook: 5 points\n"
                    "- Queen: 9 points\n\n"
                    "The King has infinite value! If you lose the King, you lose the game. "
                    "Never trade a high-value piece for a lower-value piece unless you have a brilliant tactical reason to do so."
                ),
                "challenge_fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                "expected_moves": [],
                "instruction": "Click Start Challenge to mark as completed."
            },
            {
                "id": "c1_s3",
                "title": "Knight Practice",
                "content": (
                    "Knights are tricky assassins. They move in an 'L' shape: two squares in one direction, and one square to the side. "
                    "They are the ONLY pieces on the board that can jump over other pieces!\n\n"
                    "Let's test your spatial awareness. In the next challenge, you will move your Knight to capture an undefended enemy pawn."
                ),
                "challenge_fen": "8/8/8/8/5p2/8/4N3/8 w - - 0 1",
                "expected_moves": ["e2f4"],
                "instruction": "Move the White Knight (e2) to capture the Black Pawn (f4)."
            },
            {
                "id": "c1_s4",
                "title": "Rook Practice",
                "content": (
                    "Rooks are your heavy artillery. They move in straight lines—any number of vacant squares vertically or horizontally.\n\n"
                    "In the endgame, a Rook is incredibly powerful. Let's practice a simple straight-line capture."
                ),
                "challenge_fen": "8/8/8/8/8/8/8/R6p w - - 0 1",
                "expected_moves": ["a1h1"],
                "instruction": "Move the White Rook down the rank to capture the Black Pawn."
            }
        ]
    },
    {
        "id": "chapter_2",
        "title": "Chapter 2: Secret Weapons",
        "sections": [
            {
                "id": "c2_s1",
                "title": "Castling (King Safety)",
                "content": (
                    "The center of the board is a warzone. Leaving your King there is a death sentence. "
                    "Castling is a special move that lets you tuck your King safely into a corner while simultaneously bringing your Rook into the action.\n\n"
                    "To castle, your King moves two squares toward the Rook, and the Rook jumps to the other side of the King."
                ),
                "challenge_fen": "8/8/8/8/8/8/8/4K2R w K - 0 1",
                "expected_moves": ["e1g1"],
                "instruction": "Castle Kingside (short castle) by moving your King two squares to the right."
            },
            {
                "id": "c2_s2",
                "title": "En Passant",
                "content": (
                    "The most misunderstood rule in chess! 'En Passant' is French for 'in passing'.\n\n"
                    "If an enemy pawn moves forward TWO squares from its starting position and lands exactly next to your pawn, you have the option—on the VERY NEXT TURN ONLY—to capture it as if it had only moved one square."
                ),
                "challenge_fen": "8/8/8/3pP3/8/8/8/8 w - d6 0 1",
                "expected_moves": ["e5d6"],
                "instruction": "Black just played d5. Capture it en passant by moving your pawn to d6."
            },
            {
                "id": "c2_s3",
                "title": "Pawn Promotion",
                "content": (
                    "Pawns may be weak, but they have a dream. If a pawn manages to march all the way to the opposite edge of the board, it promotes!\n\n"
                    "You can turn that pawn into a Queen, Rook, Bishop, or Knight. (Usually, you want a Queen)."
                ),
                "challenge_fen": "8/4P3/8/8/8/8/8/8 w - - 0 1",
                "expected_moves": ["e7e8"],
                "instruction": "Move the white pawn forward to promote it into a Queen!"
            }
        ]
    },
    {
        "id": "chapter_3",
        "title": "Chapter 3: The CCT Algorithm",
        "sections": [
            {
                "id": "c3_s1",
                "title": "How Masters Think",
                "content": (
                    "How do Grandmasters find brilliant moves? They use a mental algorithm to evaluate the board. "
                    "On every single turn, you must scan the board for forcing moves in this exact order: **C.C.T.**\n\n"
                    "1. **Checks**: Can I attack the enemy King?\n"
                    "2. **Captures**: Can I take an enemy piece for free or for a good trade?\n"
                    "3. **Threats**: Can I create an unavoidable attack on my next turn?\n\n"
                    "Always look for Checks first, because they force the opponent to respond instantly."
                ),
                "challenge_fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                "expected_moves": [],
                "instruction": "Memorize C.C.T. (Checks, Captures, Threats) then click Start Challenge."
            },
            {
                "id": "c3_s2",
                "title": "Finding the Check",
                "content": (
                    "Let's put the algorithm into practice. Scan the board for Checks. Is there a way to put the black King under attack safely?\n\n"
                    "Look at your pieces and imagine their paths. Find the move that forces the King to react."
                ),
                "challenge_fen": "8/8/1k6/8/8/8/8/4Q3 w - - 0 1",
                "expected_moves": ["e1b4", "e1e6", "e1g1"], # Let's just expect e1b4 as the primary answer for the lesson
                "instruction": "Move the Queen to b4 to deliver a check!"
            }
        ]
    },
    {
        "id": "chapter_4",
        "title": "Chapter 4: Opening Principles",
        "sections": [
            {
                "id": "c4_s1",
                "title": "Control the Center",
                "content": (
                    "The four squares in the very middle of the board (d4, e4, d5, e5) are the high ground. "
                    "Whoever controls the center controls the flow of the game.\n\n"
                    "You should always try to place your pawns in the center during the first few moves of the game."
                ),
                "challenge_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                "expected_moves": ["e2e4"],
                "instruction": "Play the most popular opening move: pawn to e4!"
            },
            {
                "id": "c4_s2",
                "title": "Develop Minor Pieces",
                "content": (
                    "After securing the center, your next priority is to 'develop' your minor pieces (Knights and Bishops). "
                    "Get them off the back rank and into active positions where they attack the center.\n\n"
                    "Knights before Bishops is a good rule of thumb!"
                ),
                "challenge_fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
                "expected_moves": ["g1f3"],
                "instruction": "Develop your Kingside Knight to f3 to attack the black pawn."
            }
        ]
    },
    {
        "id": "chapter_5",
        "title": "Chapter 5: Tactical Mastery",
        "sections": [
            {
                "id": "c5_s1",
                "title": "The Royal Fork",
                "content": (
                    "A 'Fork' happens when one of your pieces attacks two enemy pieces at the exact same time. "
                    "Since the opponent can only move one piece per turn, they will lose the other one!\n\n"
                    "The Knight is the ultimate forking weapon. A 'Royal Fork' attacks the King and the Queen simultaneously."
                ),
                "challenge_fen": "8/3k4/8/1q6/8/8/4N3/8 w - - 0 1",
                "expected_moves": ["e2d4"],
                "instruction": "Move the Knight to d4 to fork the King and the Queen!"
            },
            {
                "id": "c5_s2",
                "title": "The Deadly Pin",
                "content": (
                    "A 'Pin' occurs when an attacking piece threatens an enemy piece, and if that enemy piece moves, it would expose a more valuable piece (like the King) behind it.\n\n"
                    "A pinned piece is paralyzed. Use your Bishop to pin the enemy Knight to their King!"
                ),
                "challenge_fen": "8/4k3/4n3/8/8/8/1B6/8 w - - 0 1",
                "expected_moves": ["b2a3"],
                "instruction": "Move your Bishop to a3 to pin the Knight against the King."
            }
        ]
    },
    {
        "id": "chapter_6",
        "title": "Chapter 6: Execution (Checkmates)",
        "sections": [
            {
                "id": "c6_s1",
                "title": "The Back Rank Mate",
                "content": (
                    "The most common checkmate pattern for beginners! If a King is trapped behind its own pawns on the back rank, a single Rook or Queen can deliver a devastating checkmate.\n\n"
                    "Scan the board using the C.C.T. algorithm. Find the forcing check that ends the game."
                ),
                "challenge_fen": "6k1/5ppp/8/8/8/8/8/1R4K1 w - - 0 1",
                "expected_moves": ["b1b8"],
                "instruction": "Move your Rook to b8 for a Back Rank Checkmate!"
            },
            {
                "id": "c6_s2",
                "title": "Scholar's Mate",
                "content": (
                    "The infamous 4-move checkmate! It targets the weak f7 pawn, which is defended only by the Black King at the start of the game.\n\n"
                    "You have developed your Bishop to c4 and your Queen to f3. It is time to execute the final blow and claim victory."
                ),
                "challenge_fen": "r1bqk1nr/pppp1ppp/2n5/2b1p3/2B1P3/5Q2/PPPP1PPP/RNB1K1NR w KQkq - 0 4",
                "expected_moves": ["f3f7"],
                "instruction": "Capture the f7 pawn with your Queen to deliver the Scholar's Mate!"
            }
        ]
    }
]

def get_total_sections():
    """Returns the total number of sections in the curriculum."""
    count = 0
    for chapter in LEARN_CURRICULUM:
        count += len(chapter["sections"])
    return count
