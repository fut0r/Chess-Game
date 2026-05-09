"""
extract_pieces.py &#8212; Extract individual chess pieces from Chess-Pieces.svg
Renders full SVG with pygame, then crops each piece region to PNG.
"""

import pygame
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SVG_PATH = os.path.join(BASE_DIR, "Chess-Pieces.svg")
OUTPUT_DIR = os.path.join(BASE_DIR, "assets", "pieces")

# SVG viewBox: -566.7274 -103 1664.797 507.0414
# When rendered at native resolution by pygame: 1665x508 pixels
# Pixel offsets: SVG x=0 -> pixel 566.7, SVG y=0 -> pixel 103
X_OFF = 566.7
Y_OFF = 103.0

# Piece crop regions in SVG coordinates: (center_x, center_y, half_size)
# Identified by sampling the rendered sprite
PIECE_REGIONS = {
    # White pieces (top row, fill=#FFFFFF with dark outlines)
    "white_rook":   (-455, 15,   85),
    "white_knight": (-218, 5,    110),
    "white_bishop": (40,   10,   90),
    "white_queen":  (270,  0,    90),
    "white_king":   (510,  0,    90),
    "white_pawn":   (1005, 25,   75),
    # Black pieces (bottom row, same x, y shifted ~+270)
    "black_rook":   (-455, 285,  85),
    "black_knight": (-218, 275,  110),
    "black_bishop": (40,   280,  90),
    "black_queen":  (270,  275,  90),
    "black_king":   (510,  270,  90),
    "black_pawn":   (1005, 295,  75),
}

TARGET_SIZE = 200


def extract_pieces():
    """Extract all pieces from the SVG sprite sheet."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    pygame.init()
    screen = pygame.display.set_mode((200, 200), pygame.HIDDEN)

    # Load and render the full SVG
    full_img = pygame.image.load(SVG_PATH).convert_alpha()
    sprite_w, sprite_h = full_img.get_size()
    print(f"Loaded sprite: {sprite_w}x{sprite_h}")

    for piece_name, (cx, cy, half) in PIECE_REGIONS.items():
        # Convert SVG coords to pixel coords
        px_cx = int(cx + X_OFF)
        px_cy = int(cy + Y_OFF)
        px_half = int(half)

        # Crop rectangle
        left = max(0, px_cx - px_half)
        top = max(0, px_cy - px_half)
        right = min(sprite_w, px_cx + px_half)
        bottom = min(sprite_h, px_cy + px_half)

        crop_w = right - left
        crop_h = bottom - top

        # Create cropped surface
        cropped = pygame.Surface((crop_w, crop_h), pygame.SRCALPHA)
        cropped.blit(full_img, (0, 0), (left, top, crop_w, crop_h))

        # Find actual content bounds (trim transparent edges)
        min_x, min_y = crop_w, crop_h
        max_x, max_y = 0, 0
        for y in range(crop_h):
            for x in range(crop_w):
                if cropped.get_at((x, y)).a > 10:
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)

        if max_x <= min_x or max_y <= min_y:
            print(f"  SKIP {piece_name}: no content found")
            continue

        # Add small padding
        pad = 4
        min_x = max(0, min_x - pad)
        min_y = max(0, min_y - pad)
        max_x = min(crop_w - 1, max_x + pad)
        max_y = min(crop_h - 1, max_y + pad)

        content_w = max_x - min_x + 1
        content_h = max_y - min_y + 1

        # Extract content
        content = pygame.Surface((content_w, content_h), pygame.SRCALPHA)
        content.blit(cropped, (0, 0), (min_x, min_y, content_w, content_h))

        # Scale to target size (maintain aspect ratio, center)
        aspect = content_w / content_h
        if aspect > 1:
            new_w = TARGET_SIZE
            new_h = int(TARGET_SIZE / aspect)
        else:
            new_h = TARGET_SIZE
            new_w = int(TARGET_SIZE * aspect)

        scaled = pygame.transform.smoothscale(content, (new_w, new_h))

        # Center on TARGET_SIZE x TARGET_SIZE canvas
        final = pygame.Surface((TARGET_SIZE, TARGET_SIZE), pygame.SRCALPHA)
        offset_x = (TARGET_SIZE - new_w) // 2
        offset_y = (TARGET_SIZE - new_h) // 2
        final.blit(scaled, (offset_x, offset_y))

        # Save PNG
        png_path = os.path.join(OUTPUT_DIR, f"{piece_name}.png")
        pygame.image.save(final, png_path)
        print(f"  OK  {piece_name}.png  ({TARGET_SIZE}x{TARGET_SIZE})")

    # Remove old SVG files (we use PNG now)
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith('.svg'):
            os.remove(os.path.join(OUTPUT_DIR, f))
            print(f"  Removed old {f}")

    pygame.quit()
    print("\nDone! All pieces extracted to assets/pieces/")


if __name__ == "__main__":
    extract_pieces()
