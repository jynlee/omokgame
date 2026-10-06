# Omok Core + Pygame Implementation Plan

**Goal:** 15×15 자유룰 오목을 Pygame으로 실행하고, 2인 대전과 휴리스틱 AI 대전을 제공한다.

**Architecture:** `omok/board.py`(규칙)와 `omok/ai.py`(AI)는 순수 파이썬이며 pygame을 import 하지 않는다. `omok/game.py`가 pygame 화면/입력을 담당하고 board/ai를 호출한다. 로직은 pytest로 검증하고 화면은 수동 확인한다.

**Tech Stack:** Python 3.12, pygame >= 2.5, pytest >= 8

**Spec:** `docs/design/2026-10-06-omok-core-pygame-design.md`

## Global Constraints

- 작업 브랜치: `feat/omok-core` (main에서 분기). 완료 후 GitHub 웹에서 PR → main 머지
- `board.py`, `ai.py`는 pygame을 import 하지 않는다
- 상수: `SIZE = 15`, `EMPTY = 0`, `BLACK = 1`, `WHITE = 2`
- 테스트 실행은 항상 프로젝트 루트에서 `python -m pytest` (루트가 sys.path에 들어가므로 별도 설정 파일 없음)
- 화면 문구는 영어 (pygame 기본 폰트에 한글 글리프가 없음): `"2 Players"`, `"vs AI"`, `"Black's turn"`, `"White's turn"`, `"Black wins!"`, `"White wins!"`, `"Draw"`, 도움말 `"U: undo  R: restart  ESC: menu"`
- 커밋 메시지는 영어, Conventional Commits 형식
- **모든 커밋/푸시 단계는 실행 전에 사용자에게 확인을 받는다**

## Review Focus

1. 판 바깥/여백 클릭 → 무시되고 크래시 없음 (Task 3 `pixel_to_cell` 테스트)
2. AI 모드에서 사람이 이긴 직후 `U` → 사람 차례(흑)로 돌아와야 함. "무조건 2수 무르기"는 이 경우 백 차례로 끝나는 버그 (Task 3 `undo_turn` 테스트)
3. 판 가장자리에 붙은 4연속 → 바깥은 막힌 끝으로 취급하고 AI가 반대쪽 끝을 막음 (Task 2 테스트)
4. 승리수를 무른 뒤 `winner()`는 `EMPTY`, 다시 착수 가능 (Task 1 테스트)
5. 빈칸이 하나만 남은 판에서 AI가 그 칸을 반환 (Task 2 테스트)

## File Structure

| 파일 | 책임 |
|---|---|
| `requirements.txt` | `pygame>=2.5`, `pytest>=8` |
| `omok/__init__.py` | 빈 파일 |
| `omok/board.py` | 판 상태, 착수/무르기, 승리 판정 |
| `omok/ai.py` | `choose_move` 휴리스틱 |
| `omok/game.py` | 좌표 변환, 무르기 규칙, pygame 루프 `run()` |
| `main.py` | `from omok.game import run; run()` |
| `tests/test_board.py`, `tests/test_ai.py`, `tests/test_game.py` | 단위 테스트 |
| `README.md` | 소개, 설치/실행/테스트, 조작법 |

---

### Task 0: 브랜치와 환경

- [ ] **Step 1:** `git checkout -b feat/omok-core`
- [ ] **Step 2:** `requirements.txt` 작성 (위 내용), `python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`
  Expected: pygame, pytest 설치 성공. venv 생성 실패 시 `sudo apt install python3-venv` 안내

(커밋은 Task 1과 함께)

---

### Task 1: Board

**Files:**
- Create: `omok/__init__.py`, `omok/board.py`
- Test: `tests/test_board.py`

**Interfaces:**
- Produces: `SIZE, EMPTY, BLACK, WHITE`; `class Board` with `grid: list[list[int]]`, `history: list[tuple[int, int]]`, `turn: int`, `place(r: int, c: int) -> bool`, `undo() -> bool`, `winner() -> int`, `is_full() -> bool`

- [ ] **Step 1: Write the failing tests** in `tests/test_board.py`

```python
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
    # 5칸 떨어진 두 묶음 사이를 마지막에 채워 6목
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
```

- [ ] **Step 2:** `python -m pytest tests/test_board.py -v` → FAIL (`ModuleNotFoundError: omok.board`)

- [ ] **Step 3: Implement `omok/board.py`** (`omok/__init__.py`는 빈 파일)

`winner()`는 `history[-1]`의 돌만 본다. 4방향 `(0,1) (1,0) (1,1) (1,-1)` 각각 양쪽으로 같은 색을 세어 `1 + 앞 + 뒤 >= 5`이면 그 색. `place`는 범위 밖·빈칸 아님·`winner() != EMPTY`이면 `False`. `undo`는 마지막 좌표를 `EMPTY`로 되돌리고 `turn`을 그 돌의 색으로 설정.

- [ ] **Step 4:** `python -m pytest tests/test_board.py -v` → 13 passed

- [ ] **Step 5: Commit** (사용자 확인 후)

```bash
git add requirements.txt omok/__init__.py omok/board.py tests/test_board.py
git commit -m "feat: add board with placement, undo and win detection"
```

---

### Task 2: AI

**Files:**
- Create: `omok/ai.py`
- Test: `tests/test_ai.py`

**Interfaces:**
- Consumes: `Board`, `SIZE`, `EMPTY`, `BLACK`, `WHITE` (Task 1)
- Produces: `choose_move(board: Board, color: int) -> tuple[int, int]`

- [ ] **Step 1: Write the failing tests** in `tests/test_ai.py`

```python
from omok.board import Board, SIZE, EMPTY, BLACK, WHITE
from omok.ai import choose_move

def setup(black, white, turn):
    """grid를 직접 구성. history는 마지막 착수 확인용으로만 채운다."""
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
```

- [ ] **Step 2:** `python -m pytest tests/test_ai.py -v` → FAIL (`ModuleNotFoundError: omok.ai`)

- [ ] **Step 3: Implement `omok/ai.py`**

- `history`가 비면 `(SIZE // 2, SIZE // 2)`
- 후보: 빈칸 중 체비셰프 거리 2 이내에 돌이 있는 칸. 후보가 없으면 첫 빈칸 (마지막 테스트의 대비책)
- 점수 = `1.1 * evaluate(grid, r, c, color) + evaluate(grid, r, c, opponent)`, 최고점 반환. 동점은 `r`, `c` 오름차순 순회에서 먼저 찾은 것
- `evaluate`는 판을 바꾸지 않는다. 방향별 점수를 합산:

```python
SCORES = {(5, 0): 100000, (5, 1): 100000, (5, 2): 100000,
          (4, 2): 10000, (4, 1): 1000, (3, 2): 1000,
          (3, 1): 100, (2, 2): 100, (2, 1): 10}

def line_score(grid, r, c, dr, dc, color):
    n, open_ends = 1, 0
    for sign in (1, -1):
        rr, cc = r + dr * sign, c + dc * sign
        while 0 <= rr < SIZE and 0 <= cc < SIZE and grid[rr][cc] == color:
            n += 1
            rr += dr * sign
            cc += dc * sign
        if 0 <= rr < SIZE and 0 <= cc < SIZE and grid[rr][cc] == EMPTY:
            open_ends += 1
    return SCORES.get((min(n, 5), open_ends), 1)
```

- [ ] **Step 4:** `python -m pytest -v` → 19 passed (board 13 + ai 6)

- [ ] **Step 5: Commit** (사용자 확인 후)

```bash
git add omok/ai.py tests/test_ai.py
git commit -m "feat: add heuristic AI move selection"
```

---

### Task 3: Pygame 화면

**Files:**
- Create: `omok/game.py`, `main.py`
- Test: `tests/test_game.py`

**Interfaces:**
- Consumes: `Board`, `BLACK`, `WHITE`, `EMPTY`, `SIZE` (Task 1), `choose_move` (Task 2)
- Produces: 상수 `CELL = 40`, `MARGIN = 40`, `TOP = 60`; `pixel_to_cell(x: int, y: int) -> tuple[int, int] | None`; `undo_turn(board: Board, mode: str) -> None` (`mode`는 `"pvp"` 또는 `"ai"`); `run() -> None`

교차점 `(r, c)`의 픽셀 좌표: `x = MARGIN + c * CELL`, `y = TOP + MARGIN + r * CELL`. 창 크기 `(MARGIN * 2 + CELL * (SIZE - 1), TOP + MARGIN * 2 + CELL * (SIZE - 1))` = `(640, 700)`.

- [ ] **Step 1: Write the failing tests** in `tests/test_game.py`

```python
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
```

- [ ] **Step 2:** `python -m pytest tests/test_game.py -v` → FAIL (`ModuleNotFoundError: omok.game`)

- [ ] **Step 3: Implement `pixel_to_cell`, `undo_turn` in `omok/game.py`**

`pixel_to_cell`: `c = round((x - MARGIN) / CELL)`, `r = round((y - TOP - MARGIN) / CELL)`, 둘 다 `0..SIZE-1`이 아니면 `None`.
`undo_turn`: `"pvp"`면 `undo()` 1회. `"ai"`면 `undo()` 1회 후 `turn != BLACK`이고 `history`가 남아 있으면 한 번 더.
`import pygame`은 모듈 상단에 둔다 (pygame은 화면 없이도 import 가능).

- [ ] **Step 4:** `python -m pytest -v` → 25 passed

- [ ] **Step 5: Implement `run()` in `omok/game.py` and `main.py`**

- 상태 변수: `state` (`"menu"`/`"playing"`/`"over"`), `mode` (`"pvp"`/`"ai"`), `board`
- menu: 가운데 두 버튼 `"2 Players"` → `mode="pvp"`, `"vs AI"` → `mode="ai"`, 둘 다 `board = Board()`, `state="playing"`
- playing 클릭: `pixel_to_cell` → `board.place`. 성공 후 `winner()` 또는 `is_full()`이면 `over`. AI 모드이고 진행 중이면 `board.place(*choose_move(board, WHITE))` 후 같은 판정
- 키: `U` → `undo_turn(board, mode)`, `state="playing"`; `R` → 새 `Board()`, `state="playing"`; `ESC` → `state="menu"`. 키는 playing/over에서만 처리
- 그리기: 배경 `(220, 179, 92)`, 격자선 검정, 돌 반지름 `CELL // 2 - 2`, 흑 `(0,0,0)` 백 `(255,255,255)`, 마지막 수에 빨간 작은 원(반지름 4). 상단 바에 차례/결과 문구와 도움말 (Global Constraints의 문구)
- 60 FPS (`pygame.time.Clock().tick(60)`), 창 닫기 이벤트로 종료
- `main.py`: `from omok.game import run` 후 `if __name__ == "__main__": run()`

- [ ] **Step 6: Manual check** — `python main.py`
  - 2 Players: 한 판 끝까지 두어 승리 메시지 확인, `U` 1수 무르기, `R`, `ESC`
  - vs AI: AI가 즉시 응수, 4연속을 만들면 AI가 막음, 이긴 직후 `U` → 흑 차례
  - 판 바깥 클릭 무시
  - WSL에서 창이 안 뜨면 Windows PowerShell에서 Windows용 Python으로 실행해서 확인

- [ ] **Step 7: Commit** (사용자 확인 후)

```bash
git add omok/game.py main.py tests/test_game.py
git commit -m "feat: add pygame UI with menu, pvp and ai modes"
```

---

### Task 4: README와 마무리

**Files:**
- Create: `README.md`

- [ ] **Step 1:** README 작성 — 프로젝트 소개(포트폴리오/학습 목적, 자유룰), 기능, 설치(`pip install -r requirements.txt`), 실행(`python main.py`), 테스트(`python -m pytest`), 조작법(클릭, U/R/ESC), 구조(파일 표), AI 동작 요약(후보 범위, 점수표), 향후 계획(FastAPI, MCP)
- [ ] **Step 2:** `python -m pytest -v` → 25 passed
- [ ] **Step 3: Commit + push** (사용자 확인 후)

```bash
git add README.md
git commit -m "docs: add README"
git push -u origin feat/omok-core
```

- [ ] **Step 4:** 사용자에게 GitHub 웹에서 `feat/omok-core` → `main` PR 생성/머지 안내
