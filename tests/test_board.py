from omok.board import Board, SIZE, EMPTY, BLACK, WHITE


def play(moves):
    """흑/백 번갈아 착수. moves는 [(r,c), ...]"""
    b = Board()
    for r, c in moves:
        assert b.place(r, c)
    return b


def black_line(cells, filler_row=14):
    """흑은 cells에, 백은 filler_row에 흩어 두어 흑 연속만 만든다."""
    moves = []
    for i, cell in enumerate(cells):
        moves.append(cell)
        if i < len(cells) - 1:
            moves.append((filler_row, i * 2))
    return moves


def test_initial_state():
    b = Board()
    assert b.turn == BLACK and b.history == [] and b.winner() == EMPTY
    assert all(v == EMPTY for row in b.grid for v in row)


def test_horizontal_win():
    assert play(black_line([(7, c) for c in range(3, 8)])).winner() == BLACK


def test_vertical_win():
    assert play(black_line([(r, 7) for r in range(3, 8)])).winner() == BLACK


def test_diagonal_down_win():
    assert play(black_line([(i, i) for i in range(5)])).winner() == BLACK


def test_diagonal_up_win():
    assert play(black_line([(10 - i, i) for i in range(5)])).winner() == BLACK


def test_win_at_board_edge():
    assert play(black_line([(r, 14) for r in range(10, 15)], filler_row=0)).winner() == BLACK


def test_six_in_row_wins():
    # 양쪽 묶음 사이를 마지막에 채워 6목
    cells = [(7, 0), (7, 1), (7, 2), (7, 4), (7, 5), (7, 3)]
    assert play(black_line(cells)).winner() == BLACK


def test_four_is_not_win():
    assert play(black_line([(7, c) for c in range(4)])).winner() == EMPTY


def test_invalid_place():
    b = Board()
    assert b.place(-1, 0) is False
    assert b.place(0, SIZE) is False
    assert b.place(7, 7) is True
    assert b.place(7, 7) is False
    assert b.turn == WHITE and len(b.history) == 1


def test_undo_restores_state():
    b = play([(7, 7), (7, 8)])
    assert b.undo() is True
    assert b.grid[7][8] == EMPTY and b.turn == WHITE and b.history == [(7, 7)]
    assert Board().undo() is False


def test_no_place_after_win():
    b = play(black_line([(7, c) for c in range(5)]))
    assert b.place(0, 0) is False


def test_undo_winning_move_resumes_game():
    b = play(black_line([(7, c) for c in range(5)]))
    assert b.undo()
    assert b.winner() == EMPTY and b.place(7, 4)


def test_is_full():
    b = Board()
    assert not b.is_full()
    b.history = [(0, 0)] * (SIZE * SIZE)
    assert b.is_full()
