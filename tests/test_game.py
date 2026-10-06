from omok.board import Board, BLACK, WHITE
from omok.game import pixel_to_cell, undo_turn, CELL, MARGIN, TOP


def test_pixel_to_cell_exact_and_near():
    assert pixel_to_cell(MARGIN, TOP + MARGIN) == (0, 0)
    assert pixel_to_cell(MARGIN + 7 * CELL + 15, TOP + MARGIN + 7 * CELL - 15) == (7, 7)


def test_pixel_to_cell_outside():
    assert pixel_to_cell(0, 0) is None
    assert pixel_to_cell(MARGIN + 15 * CELL, TOP + MARGIN) is None
    assert pixel_to_cell(MARGIN, 10) is None


def test_undo_pvp_one_move():
    b = Board(); b.place(7, 7); b.place(7, 8)
    undo_turn(b, "pvp")
    assert len(b.history) == 1 and b.turn == WHITE


def test_undo_ai_two_moves():
    b = Board(); b.place(7, 7); b.place(7, 8)
    undo_turn(b, "ai")
    assert b.history == [] and b.turn == BLACK


def test_undo_ai_after_human_win_returns_to_black():
    b = Board()
    for c in range(4):
        b.place(7, c); b.place(0, c * 2)
    b.place(7, 4)  # 흑 승리, history 홀수
    undo_turn(b, "ai")
    assert b.turn == BLACK and len(b.history) == 8


def test_undo_empty_board_noop():
    b = Board()
    undo_turn(b, "ai")
    assert b.history == []


def test_status_text():
    from omok.game import status_text
    names = {BLACK: "소라(흑)", WHITE: "조개(백)"}
    b = Board()
    assert status_text(b, names) == "소라(흑) 차례"
    assert status_text(b, names, thinking=True) == "생각 중..."
    for c in range(4):
        b.place(7, c); b.place(0, c * 2)
    b.place(7, 4)
    assert status_text(b, names) == "소라(흑) 승리!"
    full = Board(); full.history = [(0, 0)] * 225
    assert status_text(full, names) == "무승부"


def test_thinking_dots_cycle():
    from omok.game import status_text
    names = {BLACK: "흑", WHITE: "백"}
    assert [status_text(Board(), names, thinking=True, t=t) for t in (0, 300, 600, 900)] == \
        ["생각 중.", "생각 중..", "생각 중...", "생각 중."]


def test_effect_time_counts_from_win():
    from omok.game import effect_time
    assert effect_time(now=50_000, won_at=49_000) == 1000
    assert effect_time(now=50_000, won_at=None) == 0


def test_advance_runs_at_least_once_and_finishes():
    from omok.game import advance

    def steps():
        yield
        yield
        return "done"

    gen, results = steps(), []
    while not results or not results[-1][0]:
        results.append(advance(gen, 0))
    assert results == [(False, None), (False, None), (True, "done")]


def test_bar_buttons_stay_above_board():
    from omok.game import bar_buttons
    buttons = bar_buttons()
    assert list(buttons) == ["무르기", "다시", "메뉴"]
    rects = list(buttons.values())
    for i, rect in enumerate(rects):
        assert rect.bottom < TOP and pixel_to_cell(*rect.center) is None
        assert not any(rect.colliderect(other) for other in rects[i + 1:])
