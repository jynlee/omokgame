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
