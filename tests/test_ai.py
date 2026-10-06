import random
import time

from omok.board import Board, SIZE, EMPTY, BLACK, WHITE
from omok.ai import choose_move


def setup(black, white, turn):
    """grid를 직접 구성. history는 비어 있지 않게만 채운다."""
    b = Board()
    for r, c in black:
        b.grid[r][c] = BLACK
    for r, c in white:
        b.grid[r][c] = WHITE
    b.history = list(black) + list(white)
    b.turn = turn
    return b


def test_empty_board_center():
    assert choose_move(Board(), BLACK) == (7, 7)


def test_completes_own_five():
    b = setup(black=[(0, 0), (0, 2), (2, 0), (2, 2)],
              white=[(7, c) for c in range(3, 7)], turn=WHITE)
    assert choose_move(b, WHITE) in {(7, 2), (7, 7)}


def test_blocks_opponent_open_four():
    b = setup(black=[(7, c) for c in range(3, 7)],
              white=[(0, 0), (0, 2), (2, 0), (2, 2)], turn=WHITE)
    assert choose_move(b, WHITE) in {(7, 2), (7, 7)}


def test_prefers_win_over_block():
    b = setup(black=[(3, c) for c in range(3, 7)],
              white=[(10, c) for c in range(3, 7)], turn=WHITE)
    assert choose_move(b, WHITE) in {(10, 2), (10, 7)}


def test_blocks_four_at_board_edge():
    b = setup(black=[(0, c) for c in range(4)],
              white=[(5, 5), (5, 7), (7, 5)], turn=WHITE)
    assert choose_move(b, WHITE) == (0, 4)


def test_last_empty_cell():
    b = Board()
    for r in range(SIZE):
        for c in range(SIZE):
            b.grid[r][c] = BLACK if (r + c // 2) % 2 else WHITE
    b.grid[14][14] = EMPTY
    b.history = [(0, 0)]
    assert choose_move(b, WHITE) == (14, 14)


FIVE_OWN = dict(black=[(0, 0), (0, 2), (2, 0), (2, 2)], white=[(7, c) for c in range(3, 7)], turn=WHITE)
FIVE_OPP = dict(black=[(7, c) for c in range(3, 7)], white=[(0, 0), (0, 2), (2, 0), (2, 2)], turn=WHITE)


def test_easy_always_completes_five():
    for s in range(10):
        assert choose_move(setup(**FIVE_OWN), WHITE, "easy", random.Random(s)) in {(7, 2), (7, 7)}


def test_easy_always_blocks_five():
    for s in range(10):
        assert choose_move(setup(**FIVE_OPP), WHITE, "easy", random.Random(s)) in {(7, 2), (7, 7)}


def test_easy_varies_without_forced_move():
    b = setup(black=[(7, 7)], white=[(7, 8)], turn=BLACK)
    assert len({choose_move(b, BLACK, "easy", random.Random(s)) for s in range(20)}) >= 2


def test_hard_blocks_five():
    assert choose_move(setup(**FIVE_OPP), WHITE, "hard") in {(7, 2), (7, 7)}


def test_levels_do_not_modify_grid():
    b = setup(black=[(7, 7), (8, 8), (6, 8)], white=[(7, 8), (8, 7)], turn=BLACK)
    before = [row[:] for row in b.grid]
    for level in ("easy", "normal", "hard"):
        choose_move(b, BLACK, level, random.Random(0))
        assert b.grid == before


def test_hard_beats_normal_as_both_colors():
    for hard_color in (BLACK, WHITE):
        b, worst = Board(), 0.0
        while b.winner() == EMPTY and not b.is_full():
            if b.turn == hard_color:
                t = time.perf_counter()
                move = choose_move(b, b.turn, "hard")
                worst = max(worst, time.perf_counter() - t)
            else:
                move = choose_move(b, b.turn, "normal")
            assert b.place(*move)
        assert b.winner() == hard_color
        assert worst < 2.0
