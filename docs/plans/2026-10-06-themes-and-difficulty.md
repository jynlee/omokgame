# Themes and AI Difficulty Implementation Plan

**Goal:** 테마 3종(모래사장, 칠판, 칠판(분필 돌))과 한글 글꼴, 승리 강조 효과, AI 난이도 Easy/Normal/Hard를 추가하고 README로 마무리한다.

**Architecture:** 판 배치는 `omok/layout.py`, 그리기는 `omok/themes/`의 테마 객체가 맡고 `game.py`는 테마 인터페이스만 호출한다. 난이도는 `choose_move`의 `level` 인자로 분기하며 Hard는 알파베타 negamax 깊이 5.

**Tech Stack:** Python 3.12, pygame 2.6, pytest

**Spec:** `docs/design/2026-10-06-themes-and-difficulty-design.md`

## Global Constraints

- 브랜치 `feat/omok-core`에서 계속. 이전 계획(`2026-10-06-omok-core-pygame.md`)의 Task 4(README)는 이 계획의 Task 6으로 흡수
- `board.py`, `ai.py`는 pygame을 import 하지 않는다
- 테스트는 프로젝트 루트에서 `.venv/bin/python -m pytest`
- 화면 문구는 스펙의 "화면 문구" 표 그대로 (한글)
- 커밋 메시지 영어, Conventional Commits
- **모든 커밋/푸시 전에 사용자 확인**

## Review Focus

1. 테마를 바꾼 직후 배경 캐시가 다른 테마 것으로 섞이지 않는지 (테마 객체별 캐시, Task 3/4 테스트)
2. Hard 계산 중 창이 "응답 없음"으로 보이지 않도록 "생각 중..." 프레임을 먼저 그리는지 (Task 5 수동 확인)
3. 실행 위치가 프로젝트 루트가 아니어도 글꼴을 찾는지 (패키지 기준 경로, Task 3 테스트)
4. 6목 승리 시 강조가 6칸 모두에 적용되는지 (Task 1 테스트)
5. 승리 후 `U`로 무르면 승리 효과가 사라지고 다시 둘 수 있는지 (Task 5 수동 확인, `winning_line()`은 Task 1에서 `[]` 확인)

---

### Task 1: `Board.winning_line`

**Files:** Modify `omok/board.py`; Test `tests/test_board.py`

**Interfaces:**
- Produces: `Board.winning_line() -> list[tuple[int, int]]`

- [ ] **Step 1: 실패 테스트 추가** (`play`, `black_line` 헬퍼는 기존 것)

```python
def test_winning_line_horizontal():
    b = play(black_line([(7, c) for c in range(3, 8)]))
    assert b.winning_line() == [(7, c) for c in range(3, 8)]

def test_winning_line_diagonal_in_order():
    b = play(black_line([(4 - i, 4 - i) for i in range(5)]))  # 역순으로 둬도
    assert b.winning_line() == [(i, i) for i in range(5)]

def test_winning_line_six_cells():
    cells = [(7, 0), (7, 1), (7, 2), (7, 4), (7, 5), (7, 3)]
    assert play(black_line(cells)).winning_line() == [(7, c) for c in range(6)]

def test_winning_line_empty_without_winner():
    assert play(black_line([(7, c) for c in range(4)])).winning_line() == []
    assert Board().winning_line() == []
```

- [ ] **Step 2:** `.venv/bin/python -m pytest tests/test_board.py -q` → 4 failed (`AttributeError`)
- [ ] **Step 3: 구현** — 마지막 수에서 한 방향의 연속 칸 목록을 돌려주는 내부 메서드 `_run(r, c, dr, dc) -> list[tuple]`(음의 방향 끝부터 양의 방향 끝 순서)를 만들고, `winner()`는 `len(run) >= 5`로, `winning_line()`은 처음으로 5 이상인 `run`을 반환하도록 정리
- [ ] **Step 4:** `.venv/bin/python -m pytest -q` → 29 passed
- [ ] **Step 5: Commit** (확인 후) `feat: add winning line lookup to board`

---

### Task 2: AI 난이도

**Files:** Modify `omok/ai.py`; Test `tests/test_ai.py`

**Interfaces:**
- Consumes: `Board`, `DIRECTIONS`, 기존 `SCORES`, `line_score`, `evaluate`, `candidates`
- Produces: `choose_move(board, color, level: str = "normal", rand: random.Random | None = None) -> tuple[int, int]`, `LEVELS = ("easy", "normal", "hard")`

- [ ] **Step 1: 실패 테스트 추가** (`setup` 헬퍼는 기존 것, `import random, time` 추가)

```python
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
```

- [ ] **Step 2:** `.venv/bin/python -m pytest tests/test_ai.py -q` → 새 테스트 실패 (`TypeError: unexpected argument`)
- [ ] **Step 3: 구현**

- `forced_move(grid, color) -> tuple | None`: 모든 후보 중 자신이 두면 5목(`line_score >= 100000`인 방향 존재)인 칸, 없으면 상대가 두면 5목인 칸, 없으면 `None`
- `ranked(grid, color) -> list`: 후보를 `1.1 * evaluate(own) + evaluate(opp)` 내림차순 정렬 (`sorted`는 안정 정렬이라 동점은 기존 순회 순서 유지)
- `choose_move`: 빈 판이면 중앙. `forced_move`가 있으면 그것. 이후 `normal` → `ranked(...)[0]`, `easy` → `(rand or random).choice(ranked(...)[:3])`, `hard` → `search(...)`
- Hard (시제품으로 검증한 형태, `grid`는 `board.grid` 복사본):

```python
K, DEPTH, WIN, INITIATIVE = 10, 5, 10**9, 1.5

def patterns(grid, color):
    """color 돌의 연속 구간(2개 이상)마다 (길이, 열린 끝)을 SCORES로 매겨 합산."""
    total = 0
    for r in range(SIZE):
        for c in range(SIZE):
            if grid[r][c] != color:
                continue
            for dr, dc in DIRECTIONS:
                pr, pc = r - dr, c - dc
                if 0 <= pr < SIZE and 0 <= pc < SIZE and grid[pr][pc] == color:
                    continue  # 구간의 시작점에서만 센다
                n, rr, cc = 0, r, c
                while 0 <= rr < SIZE and 0 <= cc < SIZE and grid[rr][cc] == color:
                    n, rr, cc = n + 1, rr + dr, cc + dc
                if n >= 2:
                    open_ends = sum(0 <= y < SIZE and 0 <= x < SIZE and grid[y][x] == EMPTY
                                    for y, x in ((rr, cc), (pr, pc)))
                    total += SCORES.get((min(n, 5), open_ends), 0)
    return total

def negamax(grid, color, depth, alpha, beta):
    opp = WHITE if color == BLACK else BLACK
    if depth == 0:
        return INITIATIVE * patterns(grid, color) - patterns(grid, opp)
    best = -WIN * 10
    for r, c in ranked(grid, color)[:K]:
        if makes_five(grid, r, c, color):
            return WIN + depth
        grid[r][c] = color
        value = -negamax(grid, opp, depth - 1, -beta, -alpha)
        grid[r][c] = EMPTY
        best, alpha = max(best, value), max(alpha, value)
        if alpha >= beta:
            break
    return best
```

  루트(`search`)는 `ranked(grid, color)[:K]` 각각에 착수 후 `-negamax(grid, opp, DEPTH - 1, -WIN * 10, -alpha)`로 값을 구해 최댓값의 칸을 반환 (동점은 먼저 본 칸)

- [ ] **Step 4:** `.venv/bin/python -m pytest -q` → 35 passed. 대국 테스트가 실패하면 시제품과의 차이(필수 수 검사 범위, 정렬 동점 처리)부터 확인
- [ ] **Step 5: Commit** (확인 후) `feat: add easy and hard ai difficulty levels`

---

### Task 3: 레이아웃, 글꼴, 테마 기반, 모래사장 테마

**Files:**
- Create: `omok/layout.py`, `omok/themes/__init__.py`, `omok/themes/common.py`, `omok/themes/sand.py`, `assets/fonts/*`, `tests/test_themes.py`
- Modify: `omok/game.py` (배치 상수와 `cell_center`를 `layout`에서 import)

**Interfaces:**
- Produces:
  - `omok.layout`: `CELL = 40`, `MARGIN = 40`, `TOP = 60`, `WIDTH = 640`, `HEIGHT = 700`, `cell_center(r, c) -> tuple[int, int]`
  - `omok.themes.common`: `FONT_DIR: Path` (= `Path(__file__).resolve().parents[2] / "assets" / "fonts"`), `rng(seed) -> random.Random`, `load_font(file: str, size: int) -> pygame.font.Font` (`functools.cache`, 내부에서 `pygame.font.init()`)
  - 테마 인터페이스 (스펙 표 그대로): `title`, `names`, `ink`, `background()`, `stone(surf, x, y, color, seed)`, `last_mark(surf, x, y)`, `win_effect(surf, points, t)`, `text(surf, s, size, pos, align="left", rough=1.0)`
  - `omok.themes.THEMES: list` (이 Task에서는 `[Sand()]`)

- [ ] **Step 1: 글꼴 받기**

```bash
mkdir -p assets/fonts && cd assets/fonts
B=https://github.com/google/fonts/raw/main/ofl
curl -sLo Jua-Regular.ttf $B/jua/Jua-Regular.ttf && curl -sLo Jua-OFL.txt $B/jua/OFL.txt
curl -sLo NanumPenScript-Regular.ttf $B/nanumpenscript/NanumPenScript-Regular.ttf && curl -sLo NanumPenScript-OFL.txt $B/nanumpenscript/OFL.txt
```
Expected: ttf 2개(약 2.1MB, 3.2MB), OFL 2개

- [ ] **Step 2: 실패 테스트 작성** `tests/test_themes.py`

```python
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame
import pytest
from omok.board import BLACK, WHITE
from omok.layout import WIDTH, HEIGHT, cell_center
from omok.themes import THEMES
from omok.themes.common import FONT_DIR

@pytest.fixture(scope="module", autouse=True)
def display():
    pygame.display.init(); pygame.font.init(); pygame.display.set_mode((1, 1))
    yield
    pygame.quit()

def test_font_dir_independent_of_cwd():
    assert FONT_DIR.is_absolute() and (FONT_DIR / "Jua-Regular.ttf").exists()

@pytest.mark.parametrize("theme", THEMES, ids=lambda t: t.title)
def test_background_size_and_cache(theme):
    bg = theme.background()
    assert bg.get_size() == (WIDTH, HEIGHT) and theme.background() is bg

@pytest.mark.parametrize("theme", THEMES, ids=lambda t: t.title)
def test_drawing_calls(theme):
    assert theme.title and set(theme.names) == {BLACK, WHITE}
    surf = pygame.Surface((WIDTH, HEIGHT))
    x, y = cell_center(7, 7)
    theme.stone(surf, x, y, BLACK, 1)
    theme.stone(surf, x + 40, y, WHITE, 2)
    theme.last_mark(surf, x, y)
    points = [cell_center(i, i) for i in range(5)]
    for t in (0, 1000):
        theme.win_effect(surf, points, t)
    for align in ("left", "center", "right"):
        theme.text(surf, "흑 승리!", 30, (320, 30), align)
```

- [ ] **Step 3:** `.venv/bin/python -m pytest tests/test_themes.py -q` → FAIL (`ModuleNotFoundError: omok.layout`)
- [ ] **Step 4: 구현** `layout.py`, `common.py`, `themes/__init__.py`, `sand.py`; `game.py`의 상수/`cell_center`를 `layout` import로 교체

Sand 값 (시안과 동일, RGB):
- 배경 세로 그라데이션 `(244,226,184)` → `(227,196,138)`, 알갱이 6000개 `(150,110,55)`/`(255,250,235)` 반투명, 물결 15줄 `(185,145,85,50)`
- 격자 진한 선 `(115,80,38)` 2px + 밝은 선 `(255,248,225)` 1px을 (+1,+1) 어긋나게, 화점 조약돌 `(169,128,76)` 타원
- 상단 바 `(43,134,168)` → `(92,195,212)`, 파도 경계 `y = TOP - 7 + 4·sin(x/22)`, 흰 파도 선 3px
- 소라(흑): 중심 왼쪽 원(반지름 0.64r) + 오른쪽 끝(1.05r)으로 이어진 몸통을 -0.55rad 회전, `(184,120,74)`→`(69,34,15)`, 크림색 `(245,222,180)` 나선. 조개(백): 아래 중심 부채꼴 7골, `(255,247,243)`→`(239,159,176)`, 테두리 `(197,106,128)`, 아래 작은 사다리꼴. 둘 다 아래쪽에 `(90,60,25,70)` 그림자 타원. `r = CELL // 2 - 2`
- 불가사리: 돌 중심에서 `(+0.75r, -0.7r)`, 크기 8, `(255,138,61)` 테두리 `(201,90,26)`
- 승리: 칸마다 금빛 `(255,214,80)` 원형 글로우(반지름 0.95·CELL), 알파 `0.35 + 0.45·(0.5 + 0.5·sin(t/320))`. 반짝이 30개(시드 42, 선 주변 ±17px), 크기 3~8 × `max(0, sin(t/260 + 위상))`, 금색/흰색 반반의 4꼭짓점 별
- 글씨: Jua, 흰색, 아래쪽 1px 어긋난 `(0,60,90)` 그림자. `rough` 무시
- `names = {BLACK: "소라(흑)", WHITE: "조개(백)"}`, `title = "모래사장"`, `ink = (70, 50, 25)`

글로우 원과 반투명 도형은 `pygame.SRCALPHA` Surface에 그려서 blit. 매끄러운 테두리는 `pygame.gfxdraw`의 `aacircle`/`aapolygon` 사용

- [ ] **Step 5:** `.venv/bin/python -m pytest -q` → 38 passed (themes 3 + 기존 35)
- [ ] **Step 6: Commit** (확인 후) `feat: add layout module, bundled fonts and sand theme`

---

### Task 4: 칠판 테마 2종

**Files:** Create `omok/themes/chalk.py`; Modify `omok/themes/__init__.py`; Test `tests/test_themes.py`

**Interfaces:**
- Consumes: `layout`, `common.rng`, `common.load_font`
- Produces: `class Chalk(doodle: bool = False)` (테마 인터페이스 + `_text_cache: dict`), `THEMES = [Sand(), Chalk(), Chalk(doodle=True)]`

- [ ] **Step 1: 실패 테스트 추가** — 기존 parametrize 테스트는 THEMES가 늘면 자동으로 적용됨

```python
from omok.themes.chalk import Chalk

def test_chalk_text_cached():
    theme, surf = Chalk(), pygame.Surface((WIDTH, HEIGHT))
    theme.text(surf, "흑 승리!", 34, (20, 30))
    theme.text(surf, "흑 승리!", 34, (20, 30))
    assert len(theme._text_cache) == 1

def test_three_themes_with_distinct_titles():
    assert [t.title for t in THEMES] == ["모래사장", "칠판", "칠판(분필 돌)"]
```

- [ ] **Step 2:** `.venv/bin/python -m pytest tests/test_themes.py -q` → FAIL (`ModuleNotFoundError: omok.themes.chalk`)
- [ ] **Step 3: 구현** (시안과 동일)
- 배경 `(44,74,58)`, 지우개 얼룩 70개(반지름 30~120, 흰색 알파 6~16), 가로 붓질 4줄(굵기 26, 알파 13), 가루 점 2500개, 시드 3
- 분필선: 9px 간격 마디마다 수직 방향 ±0.7px 흔들림, 5% 마디 생략, 마디별 알파 140~230, 2회 반복. 격자는 양 끝을 1~4px 넘치거나 모자라게. 색 `(238,242,232)` 굵기 2
- 화점 흰 점(반지름 3), 나무 테두리 `(124,79,43)` 12px + 안쪽 `(91,55,25)` 2px
- 입체돌: 그림자 `(0,0,0,90)` (+2,+2.5), 흑 `(109,109,109)`→`(29,29,29)`→`(0,0,0)`, 백 `(255,255,255)`→`(238,238,234)`→`(189,189,182)`, 하이라이트 중심 `(-0.35r, -0.4r)`. 방사형 그라데이션은 반지름을 줄여가며 동심원으로
- 분필 돌(`doodle`): 원 안에 기울기 45° 빗금(3.3px 간격, 알파 115~217), 흔들리는 테두리 2회, `seed`로 `rng` 고정. 흑 `(255,156,192)`, 백 `(134,193,238)`
- 마지막 수: 입체 `(232,93,117)` / 분필 `(246,246,238)` 반지름 4 원 테두리 2px
- 승리 선: 양 끝을 14% 연장, `p = min(1, (t % 3200) / 1300)`까지 분필선, 굵기 5, 입체 `(255,156,192)` / 분필 `(246,226,122)`. 시드 9 고정
- 분필 글씨(스펙 4단계): Nanum Pen Script, `(244,246,238)`. 본 글자 알파 230, (+0.8,-0.7)/(-0.6,+0.6) 어긋난 두 벌 알파 `115·rough`, 지우기 `w·h·0.09·rough`개 (폭 1~4.5, 높이 0.6~1.4, 알파 90~255), 가루 `w·0.5·rough`개. 지우기는 `BLEND_RGBA_SUB`로 알파 차감. 캐시 키 `(s, size, rough)`
- `names`: 입체 `{BLACK: "흑", WHITE: "백"}`, 분필 `{BLACK: "분홍(흑)", WHITE: "파랑(백)"}`. `title`: `"칠판"`, `"칠판(분필 돌)"`. `ink = (238, 242, 232)`
- [ ] **Step 4:** `.venv/bin/python -m pytest -q` → 44 passed
- [ ] **Step 5: Commit** (확인 후) `feat: add chalkboard themes with 3d and chalk stones`

---

### Task 5: 게임 화면 연결

**Files:** Modify `omok/game.py`; Test `tests/test_game.py`

**Interfaces:**
- Consumes: `THEMES`, `choose_move(board, color, level)`, `Board.winning_line()`, `layout`
- Produces: `status_text(board, names, thinking=False) -> str`, `draw_game(screen, theme, board, status, t)`, `draw_menu(screen, theme, buttons)`, `run()`

- [ ] **Step 1: 실패 테스트 추가**

```python
from omok.game import status_text
NAMES = {BLACK: "소라(흑)", WHITE: "조개(백)"}

def test_status_text():
    b = Board()
    assert status_text(b, NAMES) == "소라(흑) 차례"
    assert status_text(b, NAMES, thinking=True) == "생각 중..."
    for c in range(4):
        b.place(7, c); b.place(0, c * 2)
    b.place(7, 4)
    assert status_text(b, NAMES) == "소라(흑) 승리!"
    full = Board(); full.history = [(0, 0)] * 225
    assert status_text(full, NAMES) == "무승부"
```

- [ ] **Step 2:** `.venv/bin/python -m pytest tests/test_game.py -q` → FAIL (`ImportError: status_text` 또는 시그니처 불일치)
- [ ] **Step 3: 구현**
- 상태: `"menu"`, `"difficulty"`, `"playing"`, `"over"`. 변수 `theme_idx`(0), `mode`, `level`, `ai_pending`
- menu: 제목 `"오목"`(크기 72, y = HEIGHT/4), 버튼 `"2인 대전"`/`"AI 대전"` 200×60을 (WIDTH/2 ∓ 115, HEIGHT/2), 테마 줄 y = HEIGHT/2 + 110에 `"◀"`, `title`, `"▶"` (◀ ▶ 각각 50×50 클릭 영역). ←/→ 키도 순환
- difficulty: `"Easy"`, `"Normal"`, `"Hard"` 220×56 세로 배치(HEIGHT/2 - 70부터 70 간격), `"뒤로"` 아래. 클릭 시 `level` 설정 후 새 `Board`, `"playing"`. ESC/뒤로 → menu
- playing: 사람 착수 성공 후 AI 모드이고 진행 중이면 `ai_pending = True`. 루프 끝에서 화면을 그린 **다음** `ai_pending`이면 `choose_move(board, WHITE, level)` 착수 후 `False`. `ai_pending` 중 클릭 무시
- `draw_game`: 배경 blit → 돌(`seed = r * 15 + c`) → 마지막 수 → 승자 있으면 `win_effect(screen, [cell_center(*p) for p in board.winning_line()], t)` → 상태 문구(크기 32, (20, TOP/2), 왼쪽, rough 1.0) → 도움말 `"U 무르기 | R 다시 | ESC 메뉴"`(크기 20, (WIDTH-20, TOP/2), 오른쪽, rough 0.3)
- 메뉴 버튼은 `theme.ink` 테두리 3px, 모서리 10, 글씨는 `theme.text(..., align="center")`
- `pixel_to_cell`, `undo_turn` 유지
- [ ] **Step 4:** `.venv/bin/python -m pytest -q` → 45 passed
- [ ] **Step 5: 수동 확인** — `wsl .venv/bin/python main.py` (사용자가 Windows 터미널에서)
  - 테마 3종을 메뉴에서 돌려보며 배경이 즉시 바뀌는지
  - 각 테마로 한 판: 돌 모양, 마지막 수, 승리 효과(6목 포함 가능하면), 승리 후 `U`로 효과가 사라지는지
  - Easy/Normal/Hard 한 판씩, Hard에서 "생각 중..." 표시 후 1초 안팎으로 응수하는지
- [ ] **Step 6: Commit** (확인 후) `feat: wire themes, korean text and difficulty menu into game`

---

### Task 6: README, 스크린샷, 푸시, PR

**Files:** Create `README.md`, `docs/screenshots/{menu,sand,chalk,chalk-doodle}.png`

- [ ] **Step 1: 스크린샷** — `SDL_VIDEODRIVER=dummy`로 각 테마의 메뉴 1장(모래사장)과 승리 장면 3장을 `draw_menu`/`draw_game`으로 그려 `pygame.image.save` (일회성 명령, 스크립트 파일은 커밋하지 않음). 승리 장면은 시안의 착수 순서 사용
- [ ] **Step 2: README** — 소개(포트폴리오/학습, 자유룰), 스크린샷, 기능(2인/AI 3단계/테마 3종), 설치·실행·테스트, 조작법, 구조 표, AI 설명(휴리스틱 점수표, Easy 무작위, Hard 알파베타 깊이 5와 평가 함수), 글꼴 라이선스(SIL OFL 1.1, 출처), 향후 계획(FastAPI, MCP, exe)
- [ ] **Step 3:** `.venv/bin/python -m pytest -q` → 45 passed
- [ ] **Step 4: Commit + push** (확인 후) `docs: add README with screenshots`, `git push -u origin feat/omok-core`
- [ ] **Step 5: PR** (확인 후) `gh`가 로그인되어 있으면 `gh pr create --base main --title "feat: omok core with pygame ui, themes and ai levels" --body <요약>`, 아니면 웹 생성 안내
