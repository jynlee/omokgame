import random

import pygame

from omok.board import Board, SIZE, EMPTY, BLACK, WHITE
from omok.ai import choose_move
from omok.layout import CELL, MARGIN, TOP, WIDTH, HEIGHT, cell_center
from omok.themes import THEMES

HELP = "U 무르기 | R 다시 | ESC 메뉴"
LEVEL_LABELS = {"Easy": "easy", "Normal": "normal", "Hard": "hard"}
AI_DELAY_MS = (600, 1200)  # AI가 고민하는 듯 보이는 최소 시간 (긴장감용)


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


def status_text(board, names, thinking=False, t=None):
    if thinking:
        return "생각 중" + ("..." if t is None else "." * (1 + t // 300 % 3))
    w = board.winner()
    if w != EMPTY:
        return f"{names[w]} 승리!"
    if board.is_full():
        return "무승부"
    return f"{names[board.turn]} 차례"


def effect_time(now, won_at):
    """승리 효과용 시간: 이긴 순간부터 잰다 (애니메이션이 처음부터 재생되도록)."""
    return 0 if won_at is None else now - won_at


def draw_game(screen, theme, board, status, t):
    screen.blit(theme.background(), (0, 0))
    for r in range(SIZE):
        for c in range(SIZE):
            if board.grid[r][c] != EMPTY:
                theme.stone(screen, *cell_center(r, c), board.grid[r][c])
    if board.history:
        theme.last_mark(screen, *cell_center(*board.history[-1]))
    line = board.winning_line()
    if line:
        theme.win_effect(screen, [cell_center(*p) for p in line], t)
    theme.text(screen, status, 32, (20, TOP // 2 - 4))
    theme.text(screen, HELP, 20, (WIDTH - 20, TOP // 2 - 4), "right", rough=.3)


def menu_buttons():
    """화면별 버튼 영역. 키는 버튼 이름."""
    cx, cy = WIDTH // 2, HEIGHT // 2
    menu = {"2인 대전": pygame.Rect(0, 0, 200, 60), "AI 대전": pygame.Rect(0, 0, 200, 60),
            "◀": pygame.Rect(0, 0, 50, 50), "▶": pygame.Rect(0, 0, 50, 50)}
    menu["2인 대전"].center, menu["AI 대전"].center = (cx - 115, cy), (cx + 115, cy)
    menu["◀"].center, menu["▶"].center = (cx - 160, cy + 110), (cx + 160, cy + 110)
    levels = {}
    for i, label in enumerate([*LEVEL_LABELS, "뒤로"]):
        levels[label] = pygame.Rect(0, 0, 220, 56)
        levels[label].center = (cx, cy - 70 + i * 70 + (10 if label == "뒤로" else 0))
    return {"menu": menu, "difficulty": levels}


def draw_menu(screen, theme, buttons, title_y=HEIGHT // 4):
    screen.blit(theme.background(), (0, 0))
    panel = pygame.Surface((520, 470), pygame.SRCALPHA)
    panel.fill((*theme.background().get_at((WIDTH // 2, HEIGHT - 30))[:3], 225))
    screen.blit(panel, panel.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 15)))
    theme.text(screen, "오목", 80, (WIDTH // 2, title_y), "center", rough=.6, color=theme.ink)
    for label, rect in buttons.items():
        if label in ("◀", "▶"):  # 글꼴에 화살표 글리프가 없어 도형으로 그린다
            x, y = rect.center
            d = -1 if label == "◀" else 1
            pygame.draw.polygon(screen, theme.ink, [(x - 9 * d, y - 13), (x - 9 * d, y + 13), (x + 12 * d, y)])
            continue
        pygame.draw.rect(screen, theme.ink, rect, 3, border_radius=10)
        theme.text(screen, label, 30, rect.center, "center", rough=.3, color=theme.ink)
    if "◀" in buttons:
        theme.text(screen, theme.title, 30, (WIDTH // 2, buttons["◀"].centery), "center", rough=.3, color=theme.ink)


def run():
    # 소리를 쓰지 않으므로 화면과 폰트만 초기화 (WSL 등에서 오디오 경고 방지)
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Omok")
    clock = pygame.time.Clock()
    buttons = menu_buttons()

    state, mode, level, theme_idx = "menu", "pvp", "normal", 0
    board, ai_pending, ai_move, ai_due, won_at = Board(), False, None, 0, None

    def finished():
        return board.winner() != EMPTY or board.is_full()

    running = True
    while running:
        theme = THEMES[theme_idx]
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                hit = next((label for label, rect in buttons.get(state, {}).items()
                            if rect.collidepoint(event.pos)), None)
                if state == "menu" and hit:
                    if hit in ("◀", "▶"):
                        theme_idx = (theme_idx + (1 if hit == "▶" else -1)) % len(THEMES)
                    elif hit == "2인 대전":
                        mode, board, state = "pvp", Board(), "playing"
                    else:
                        state = "difficulty"
                elif state == "difficulty" and hit:
                    if hit == "뒤로":
                        state = "menu"
                    else:
                        mode, level, board, state = "ai", LEVEL_LABELS[hit], Board(), "playing"
                elif state == "playing" and not ai_pending:
                    cell = pixel_to_cell(*event.pos)
                    if cell and board.place(*cell):
                        if finished():
                            state = "over"
                        elif mode == "ai":
                            ai_pending, ai_move = True, None
                            ai_due = pygame.time.get_ticks() + random.randint(*AI_DELAY_MS)
            elif event.type == pygame.KEYDOWN:
                if state == "menu" and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    theme_idx = (theme_idx + (1 if event.key == pygame.K_RIGHT else -1)) % len(THEMES)
                elif state == "difficulty" and event.key == pygame.K_ESCAPE:
                    state = "menu"
                elif state in ("playing", "over") and event.key in (pygame.K_u, pygame.K_r, pygame.K_ESCAPE):
                    ai_pending = False  # 고민 중에 판을 바꾸면 준비해 둔 AI 수는 버린다
                    if event.key == pygame.K_u:
                        undo_turn(board, mode)
                        state = "playing"
                    elif event.key == pygame.K_r:
                        board, state = Board(), "playing"
                    elif event.key == pygame.K_ESCAPE:
                        state = "menu"

        theme = THEMES[theme_idx]
        if state in ("menu", "difficulty"):
            draw_menu(screen, theme, buttons[state])
        else:
            now = pygame.time.get_ticks()
            # 승리, 무르기, 다시 시작 어느 경로든 승패 상태를 보고 승리 시각을 맞춘다
            if board.winner() == EMPTY:
                won_at = None
            elif won_at is None:
                won_at = now
            status = status_text(board, theme.names, thinking=ai_pending, t=now)
            draw_game(screen, theme, board, status, effect_time(now, won_at))
        pygame.display.flip()

        # "생각 중"을 먼저 화면에 보여준 다음 계산하고, 최소 고민 시간이 지나면 둔다
        if ai_pending:
            if ai_move is None:
                ai_move = choose_move(board, WHITE, level)
                pygame.event.clear(pygame.MOUSEBUTTONDOWN)  # 계산 중 눌린 클릭은 버린다
            if pygame.time.get_ticks() >= ai_due:
                board.place(*ai_move)
                ai_pending = False
                if finished():
                    state = "over"
        clock.tick(60)

    pygame.quit()
