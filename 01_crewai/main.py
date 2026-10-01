import random
import sys
import pygame

# --- CONSTANTS & CONFIGURATION ---
GRID_WIDTH = 10
GRID_HEIGHT = 20
BLOCK_SIZE = 30

PLAY_WIDTH = GRID_WIDTH * BLOCK_SIZE   # 300 px
PLAY_HEIGHT = GRID_HEIGHT * BLOCK_SIZE # 600 px
SIDE_PANEL_WIDTH = 200
WINDOW_WIDTH = PLAY_WIDTH + SIDE_PANEL_WIDTH # 500 px
WINDOW_HEIGHT = PLAY_HEIGHT                  # 600 px

FPS = 60

# Colors
BLACK = (0, 0, 0)
DARK_GRAY = (20, 20, 25)
GRID_LINE_COLOR = (40, 40, 50)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
RED = (230, 50, 50)

# Tetromino Colors
SHAPE_COLORS = {
    'I': (0, 240, 240),    # Cyan
    'J': (0, 0, 240),      # Blue
    'L': (240, 160, 0),    # Orange
    'O': (240, 240, 0),    # Yellow
    'S': (0, 240, 0),      # Green
    'T': (160, 0, 240),    # Purple
    'Z': (240, 0, 0)       # Red
}

# Tetromino Matrices
SHAPES = {
    'I': [
        [[0, 0, 0, 0],
         [1, 1, 1, 1],
         [0, 0, 0, 0],
         [0, 0, 0, 0]],
        [[0, 0, 1, 0],
         [0, 0, 1, 0],
         [0, 0, 1, 0],
         [0, 0, 1, 0]],
        [[0, 0, 0, 0],
         [0, 0, 0, 0],
         [1, 1, 1, 1],
         [0, 0, 0, 0]],
        [[0, 1, 0, 0],
         [0, 1, 0, 0],
         [0, 1, 0, 0],
         [0, 1, 0, 0]]
    ],
    'J': [
        [[1, 0, 0],
         [1, 1, 1],
         [0, 0, 0]],
        [[0, 1, 1],
         [0, 1, 0],
         [0, 1, 0]],
        [[0, 0, 0],
         [1, 1, 1],
         [0, 0, 1]],
        [[0, 1, 0],
         [0, 1, 0],
         [1, 1, 0]]
    ],
    'L': [
        [[0, 0, 1],
         [1, 1, 1],
         [0, 0, 0]],
        [[0, 1, 0],
         [0, 1, 0],
         [0, 1, 1]],
        [[0, 0, 0],
         [1, 1, 1],
         [1, 0, 0]],
        [[1, 1, 0],
         [0, 1, 0],
         [0, 1, 0]]
    ],
    'O': [
        [[1, 1],
         [1, 1]]
    ],
    'S': [
        [[0, 1, 1],
         [1, 1, 0],
         [0, 0, 0]],
        [[0, 1, 0],
         [0, 1, 1],
         [0, 0, 1]],
        [[0, 0, 0],
         [0, 1, 1],
         [1, 1, 0]],
        [[1, 0, 0],
         [1, 1, 0],
         [0, 1, 0]]
    ],
    'T': [
        [[0, 1, 0],
         [1, 1, 1],
         [0, 0, 0]],
        [[0, 1, 0],
         [0, 1, 1],
         [0, 1, 0]],
        [[0, 0, 0],
         [1, 1, 1],
         [0, 1, 0]],
        [[0, 1, 0],
         [1, 1, 0],
         [0, 1, 0]]
    ],
    'Z': [
        [[1, 1, 0],
         [0, 1, 1],
         [0, 0, 0]],
        [[0, 0, 1],
         [0, 1, 1],
         [0, 1, 0]],
        [[0, 0, 0],
         [1, 1, 0],
         [0, 1, 1]],
        [[0, 1, 0],
         [1, 1, 0],
         [1, 0, 0]]
    ]
}


class Piece:
    """Represents a falling Tetromino piece."""
    def __init__(self, shape_name):
        self.shape_name = shape_name
        self.rotations = SHAPES[shape_name]
        self.color = SHAPE_COLORS[shape_name]
        self.rotation_idx = 0
        self.matrix = self.rotations[self.rotation_idx]
        self.x = GRID_WIDTH // 2 - len(self.matrix[0]) // 2
        self.y = 0

    def get_shape(self):
        return self.rotations[self.rotation_idx % len(self.rotations)]


def create_grid():
    """Create a 10x20 grid initialized with black/empty RGB tuples."""
    return [[BLACK for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]


def get_random_piece():
    """Spawn a random Tetromino piece."""
    shape_name = random.choice(list(SHAPES.keys()))
    return Piece(shape_name)


def valid_move(piece, grid, offset_x=0, offset_y=0, rotation_offset=0):
    """Check if piece movement or rotation is valid and within bounds."""
    next_rot_idx = (piece.rotation_idx + rotation_offset) % len(piece.rotations)
    shape = piece.rotations[next_rot_idx]

    for row_idx, row in enumerate(shape):
        for col_idx, cell in enumerate(row):
            if cell:
                x = piece.x + col_idx + offset_x
                y = piece.y + row_idx + offset_y

                # Wall and floor boundaries
                if x < 0 or x >= GRID_WIDTH or y >= GRID_HEIGHT:
                    return False
                # Collision with locked blocks on grid
                if y >= 0 and grid[y][x] != BLACK:
                    return False
    return True


def lock_piece(piece, grid):
    """Lock the piece's color into the board matrix."""
    shape = piece.get_shape()
    for row_idx, row in enumerate(shape):
        for col_idx, cell in enumerate(row):
            if cell:
                x = piece.x + col_idx
                y = piece.y + row_idx
                if 0 <= y < GRID_HEIGHT and 0 <= x < GRID_WIDTH:
                    grid[y][x] = piece.color


def clear_rows(grid):
    """Detect and remove full rows, shift top rows down, return (points, cleared_count)."""
    full_rows = []
    for y in range(GRID_HEIGHT):
        if all(cell != BLACK for cell in grid[y]):
            full_rows.append(y)

    cleared_count = len(full_rows)
    for y in full_rows:
        del grid[y]
        grid.insert(0, [BLACK for _ in range(GRID_WIDTH)])

    # Standard Tetris scoring table
    score_table = {0: 0, 1: 100, 2: 300, 3: 500, 4: 800}
    return score_table.get(cleared_count, cleared_count * 200), cleared_count


def draw_block(surface, x, y, color):
    """Draw a single block with a subtle border effect."""
    rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
    pygame.draw.rect(surface, color, rect)
    # Highlight border for 3D block look
    pygame.draw.rect(surface, (min(color[0]+30, 255), min(color[1]+30, 255), min(color[2]+30, 255)), rect, 1)


def draw_grid_lines(surface):
    """Draw grid lines over the play area."""
    for x in range(GRID_WIDTH + 1):
        pygame.draw.line(surface, GRID_LINE_COLOR, (x * BLOCK_SIZE, 0), (x * BLOCK_SIZE, PLAY_HEIGHT))
    for y in range(GRID_HEIGHT + 1):
        pygame.draw.line(surface, GRID_LINE_COLOR, (0, y * BLOCK_SIZE), (PLAY_WIDTH, y * BLOCK_SIZE))


def draw_side_panel(surface, font, small_font, score, lines, next_piece):
    """Render score, lines, next piece preview, and controls instructions."""
    panel_rect = pygame.Rect(PLAY_WIDTH, 0, SIDE_PANEL_WIDTH, PLAY_HEIGHT)
    pygame.draw.rect(surface, DARK_GRAY, panel_rect)
    pygame.draw.line(surface, GRAY, (PLAY_WIDTH, 0), (PLAY_WIDTH, PLAY_HEIGHT), 2)

    # Score
    score_lbl = font.render("SCORE", True, WHITE)
    score_val = font.render(str(score), True, WHITE)
    surface.blit(score_lbl, (PLAY_WIDTH + 20, 30))
    surface.blit(score_val, (PLAY_WIDTH + 20, 60))

    # Lines Cleared
    lines_lbl = font.render("LINES", True, WHITE)
    lines_val = font.render(str(lines), True, WHITE)
    surface.blit(lines_lbl, (PLAY_WIDTH + 20, 120))
    surface.blit(lines_val, (PLAY_WIDTH + 20, 150))

    # Next Piece Preview
    next_lbl = font.render("NEXT", True, WHITE)
    surface.blit(next_lbl, (PLAY_WIDTH + 20, 220))

    if next_piece:
        matrix = next_piece.get_shape()
        preview_x = PLAY_WIDTH + 40
        preview_y = 260
        for r_idx, row in enumerate(matrix):
            for c_idx, cell in enumerate(row):
                if cell:
                    px = preview_x + c_idx * 25
                    py = preview_y + r_idx * 25
                    rect = pygame.Rect(px, py, 25, 25)
                    pygame.draw.rect(surface, next_piece.color, rect)
                    pygame.draw.rect(surface, WHITE, rect, 1)

    # Controls Info
    controls = [
        "CONTROLS:",
        "Left / Right: Move",
        "Up / Space: Rotate",
        "Down: Soft Drop",
        "R: Restart Game"
    ]
    for idx, line in enumerate(controls):
        txt = small_font.render(line, True, GRAY)
        surface.blit(txt, (PLAY_WIDTH + 15, 420 + idx * 22))


def draw_game_over(surface, font, small_font):
    """Draw Game Over modal overlay."""
    overlay = pygame.Surface((PLAY_WIDTH, PLAY_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    surface.blit(overlay, (0, 0))

    go_text = font.render("GAME OVER", True, RED)
    restart_text = small_font.render("Press 'R' to Restart", True, WHITE)

    text_rect = go_text.get_rect(center=(PLAY_WIDTH // 2, PLAY_HEIGHT // 2 - 20))
    restart_rect = restart_text.get_rect(center=(PLAY_WIDTH // 2, PLAY_HEIGHT // 2 + 20))

    surface.blit(go_text, text_rect)
    surface.blit(restart_text, restart_rect)


def main():
    pygame.init()
    pygame.font.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Tetris")

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("sans-serif", 28, bold=True)
    small_font = pygame.font.SysFont("sans-serif", 18)

    grid = create_grid()
    current_piece = get_random_piece()
    next_piece = get_random_piece()

    score = 0
    lines_cleared_total = 0
    game_over = False

    fall_time = 0
    fall_speed = 0.5  # Seconds per step

    running = True
    while running:
        delta_time = clock.tick(FPS) / 1000.0
        fall_time += delta_time

        # --- EVENT HANDLING ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if event.type == pygame.KEYDOWN:
                if game_over:
                    if event.key == pygame.K_r:
                        grid = create_grid()
                        current_piece = get_random_piece()
                        next_piece = get_random_piece()
                        score = 0
                        lines_cleared_total = 0
                        game_over = False
                        fall_time = 0
                    continue

                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    if valid_move(current_piece, grid, offset_x=-1):
                        current_piece.x -= 1

                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    if valid_move(current_piece, grid, offset_x=1):
                        current_piece.x += 1

                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    if valid_move(current_piece, grid, offset_y=1):
                        current_piece.y += 1
                        score += 1

                elif event.key == pygame.K_UP or event.key == pygame.K_SPACE:
                    if valid_move(current_piece, grid, rotation_offset=1):
                        current_piece.rotation_idx = (current_piece.rotation_idx + 1) % len(current_piece.rotations)

                elif event.key == pygame.K_r:
                    grid = create_grid()
                    current_piece = get_random_piece()
                    next_piece = get_random_piece()
                    score = 0
                    lines_cleared_total = 0
                    game_over = False

        # --- GRAVITY / AUTOMATIC FALL ---
        if not game_over and fall_time >= fall_speed:
            fall_time = 0
            if valid_move(current_piece, grid, offset_y=1):
                current_piece.y += 1
            else:
                lock_piece(current_piece, grid)
                pts, lines = clear_rows(grid)
                score += pts
                lines_cleared_total += lines

                # Spawn next piece
                current_piece = next_piece
                next_piece = get_random_piece()

                # Check game over condition
                if not valid_move(current_piece, grid):
                    game_over = True

        # --- RENDERING ---
        screen.fill(BLACK)

        # Draw locked grid blocks
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if grid[y][x] != BLACK:
                    draw_block(screen, x, y, grid[y][x])

        # Draw current piece
        if current_piece and not game_over:
            shape = current_piece.get_shape()
            for row_idx, row in enumerate(shape):
                for col_idx, cell in enumerate(row):
                    if cell:
                        px = current_piece.x + col_idx
                        py = current_piece.y + row_idx
                        if py >= 0:
                            draw_block(screen, px, py, current_piece.color)

        # Draw grid lines
        draw_grid_lines(screen)

        # Draw side panel
        draw_side_panel(screen, font, small_font, score, lines_cleared_total, next_piece)

        # Draw Game Over overlay if applicable
        if game_over:
            draw_game_over(screen, font, small_font)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
