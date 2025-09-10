import os
import random

# --- Constants ---
VIEWPORT_WIDTH = 40
VIEWPORT_HEIGHT = 20
MAX_PLACEMENT_TRIES = 50  # Max attempts to place a sprite without overlapping

# Build a robust path to the sprites directory relative to this script's location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SPRITES_DIR = os.path.join(SCRIPT_DIR, "sprites")

# ANSI color codes for styling
COLORS = {
    "default": "\033[0m",
    "rock": "\033[90m",   # Dark Grey
    "tree": "\033[32m",   # Green
    "npc": "\033[93m",    # Yellow
    "monster": "\033[91m", # Red
}

def load_sprite(filename):
    """Loads a multi-line ASCII sprite from a file."""
    filepath = os.path.join(SPRITES_DIR, filename)
    try:
        with open(filepath, 'r') as f:
            # Strip trailing newlines from each line
            return [line.rstrip('\n') for line in f.readlines()]
    except FileNotFoundError:
        print(f"Warning: Sprite file not found: {filepath}")
        return None

def check_overlap(viewport, sprite_lines, x, y):
    """Checks if placing a sprite at (x, y) would overlap with existing content."""
    sprite_height = len(sprite_lines)
    for i, line in enumerate(sprite_lines):
        sprite_width = len(line)
        if y + i >= VIEWPORT_HEIGHT or x + sprite_width > VIEWPORT_WIDTH:
            return True # Sprite is out of bounds

        for j, char in enumerate(line):
            if char != ' ' and viewport[y + i][x + j] != ' ':
                return True  # Overlap detected
    return False

def place_sprite(viewport, sprite_lines, x, y, color_code):
    """Places a colored sprite onto the viewport grid."""
    reset_color = COLORS["default"]
    for i, line in enumerate(sprite_lines):
        for j, char in enumerate(line):
            if char != ' ':
                viewport[y + i][x + j] = f"{color_code}{char}{reset_color}"

def generate_viewport(sprite_files):
    """
    Generates a complete viewport with randomly placed, non-overlapping sprites.
    """
    # Initialize an empty viewport grid
    viewport = [[' ' for _ in range(VIEWPORT_WIDTH)] for _ in range(VIEWPORT_HEIGHT)]

    sprites_to_place = []
    for filename in sprite_files:
        sprite_lines = load_sprite(filename)
        if sprite_lines:
            sprites_to_place.append({'filename': filename, 'lines': sprite_lines})

    # Randomize order to avoid placement bias
    random.shuffle(sprites_to_place)

    for sprite_data in sprites_to_place:
        sprite_name = os.path.splitext(sprite_data['filename'])[0]
        color = COLORS.get(sprite_name, COLORS["default"])
        sprite_lines = sprite_data['lines']
        
        sprite_height = len(sprite_lines)
        sprite_width = max(len(line) for line in sprite_lines) if sprite_lines else 0

        # Try to place the sprite without overlapping
        for _ in range(MAX_PLACEMENT_TRIES):
            # Determine random coordinates
            rand_x = random.randint(0, VIEWPORT_WIDTH - sprite_width)
            rand_y = random.randint(0, VIEWPORT_HEIGHT - sprite_height)

            if not check_overlap(viewport, sprite_lines, rand_x, rand_y):
                place_sprite(viewport, sprite_lines, rand_x, rand_y, color)
                break # Placement successful, move to next sprite

    # Convert the grid of characters into a list of strings for display
    return ["".join(row) for row in viewport]

def display_viewport(viewport_lines, title="Viewport", exits=None):
    """Prints a formatted viewport to the console."""
    exits = exits or []

    # --- Top Border ---
    top_border = list("+" + "-" * VIEWPORT_WIDTH + "+")
    if 'north' in exits:
        mid = len(top_border) // 2
        top_border[mid] = '^'
    print("".join(top_border))

    # --- Content with Side Borders ---
    mid_row = VIEWPORT_HEIGHT // 2
    for i, line in enumerate(viewport_lines):
        # Ensure the line is exactly the viewport width for clean borders
        # To calculate the visible length, we remove all ANSI escape codes.
        visible_line = line
        for color_code in COLORS.values():
            visible_line = visible_line.replace(color_code, "")
        
        padding = ' ' * (VIEWPORT_WIDTH - len(visible_line))
        
        left_border = '<' if 'west' in exits and i == mid_row else '|'
        right_border = '>' if 'east' in exits and i == mid_row else '|'

        print(f"{left_border}{line}{padding}{right_border}")

    # --- Bottom Border ---
    bottom_border = list("+" + "-" * VIEWPORT_WIDTH + "+")
    if 'south' in exits:
        mid = len(bottom_border) // 2
        bottom_border[mid] = 'v'
    print("".join(bottom_border))
    print()

def create_sprite_files():
    """Creates the sprite directory and necessary text files."""
    if not os.path.exists(SPRITES_DIR):
        os.makedirs(SPRITES_DIR)

    sprite_data = {
        "rock.txt": "  RR\nRRRR\n RRR",
        "tree.txt": "  T\n TTT\nTTTTT\n  T",
        "npc.txt": " N\n/N\\\n/ \\",
        "monster.txt": "  M\n /M\\\n M M"
    }

    for filename, content in sprite_data.items():
        with open(os.path.join(SPRITES_DIR, filename), 'w') as f:
            f.write(content)
    print(f"Created sprite files in '{SPRITES_DIR}/' directory.")


if __name__ == "__main__":
    # Ensure sprite files exist for the demo
    create_sprite_files()

    # Define the sprites to be included in the scene
    sprites_to_render = ["rock.txt", "tree.txt", "npc.txt", "monster.txt", "tree.txt"]

    print("\nGenerating example viewports...\n")

    # Generate and display a unique viewport for each cardinal direction
    # Example exits for demonstration purposes
    example_exits_map = {"North": ["south", "east"], "East": ["west"], "South": ["north"], "West": ["east", "north", "south"]}
    for direction, exits in example_exits_map.items():
        viewport = generate_viewport(sprites_to_render)
        display_viewport(viewport, title=f"View to the {direction}", exits=exits)