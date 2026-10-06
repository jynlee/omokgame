import pygame

from omok.board import Board, SIZE, EMPTY, BLACK, WHITE
from omok.ai import choose_move
from omok.layout import CELL, MARGIN, TOP, WIDTH, HEIGHT, cell_center

BG = (220, 179, 92)
LINE = (0, 0, 0)
STONE = {BLACK: (0, 0, 0), WHITE: (255, 255, 255)}
LAST_MARK = (220, 30, 30)
NAMES = {BLACK: "Black", WHITE: "White"}
HELP = "U: undo  R: restart  ESC: menu"


def pixel_to_cell(x, y):
    """클릭 픽셀을 가장 가까운 교차점 (r, c)로. 판 밖이면 None."""
    c = round((x - MARGIN) / CELL)
    r = round((y - TOP - MARGIN) / CELL)
    if 0 <= r < SIZE and 0 <= c < SIZE:
        return r, c
    return None


def undo_turn(board, mode):
    """pvp는 1수, ai는 사람(흑) 차례가 될 때까지 무르기."""
    board.undo()
    if mode == "ai" and board.turn != BLACK and board.history:
        board.undo()


def status_text(board):
    w = board.winner()
    if w != EMPTY:
        return f"{NAMES[w]} wins!"
    if board.is_full():
        return "Draw"
    return f"{NAMES[board.turn]}'s turn"


def draw_board(screen, font, board):
    screen.fill(BG)
    for i in range(SIZE):
        pygame.draw.line(screen, LINE, cell_center(i, 0), cell_center(i, SIZE - 1))
        pygame.draw.line(screen, LINE, cell_center(0, i), cell_center(SIZE - 1, i))
    for r in range(SIZE):
        for c in range(SIZE):
            if board.grid[r][c] != EMPTY:
                pygame.draw.circle(screen, STONE[board.grid[r][c]], cell_center(r, c), CELL // 2 - 2)
    if board.history:
        pygame.draw.circle(screen, LAST_MARK, cell_center(*board.history[-1]), 4)
    screen.blit(font.render(status_text(board), True, LINE), (MARGIN, 18))
    help_img = font.render(HELP, True, LINE)
    screen.blit(help_img, (WIDTH - MARGIN - help_img.get_width(), 18))


def draw_menu(screen, font, buttons):
    screen.fill(BG)
    title = pygame.font.Font(None, 80).render("Omok", True, LINE)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 3)))
    for label, rect in buttons.items():
        pygame.draw.rect(screen, LINE, rect, 2, border_radius=8)
        img = font.render(label, True, LINE)
        screen.blit(img, img.get_rect(center=rect.center))


def run():
    # 소리를 쓰지 않으므로 화면과 폰트만 초기화 (WSL 등에서 오디오 경고 방지)
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Omok")
    font = pygame.font.Font(None, 30)
    clock = pygame.time.Clock()
    buttons = {
        "2 Players": pygame.Rect(0, 0, 220, 60),
        "vs AI": pygame.Rect(0, 0, 220, 60),
    }
    buttons["2 Players"].center = (WIDTH // 2, HEIGHT // 2)
    buttons["vs AI"].center = (WIDTH // 2, HEIGHT // 2 + 90)

    state, mode, board = "menu", "pvp", Board()

    def finished():
        return board.winner() != EMPTY or board.is_full()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == "menu":
                    for label, rect in buttons.items():
                        if rect.collidepoint(event.pos):
                            mode = "pvp" if label == "2 Players" else "ai"
                            board, state = Board(), "playing"
                elif state == "playing":
                    cell = pixel_to_cell(*event.pos)
                    if cell and board.place(*cell):
                        if not finished() and mode == "ai":
                            board.place(*choose_move(board, WHITE))
                        if finished():
                            state = "over"
            elif event.type == pygame.KEYDOWN and state in ("playing", "over"):
                if event.key == pygame.K_u:
                    undo_turn(board, mode)
                    state = "playing"
                elif event.key == pygame.K_r:
                    board, state = Board(), "playing"
                elif event.key == pygame.K_ESCAPE:
                    state = "menu"

        if state == "menu":
            draw_menu(screen, font, buttons)
        else:
            draw_board(screen, font, board)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
