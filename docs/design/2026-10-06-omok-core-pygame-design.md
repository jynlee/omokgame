# 오목 코어 + Pygame 설계

- 날짜: 2026-10-06
- 단계: 하위 프로젝트 1/4 (코어 + Pygame → FastAPI/클라우드 → MCP → A2A)

## 목적

포트폴리오 및 학습용 Python 오목 게임. 로컬에서 `python main.py`로 실행하는 Pygame GUI.

성공 기준:
- 클론 후 `pip install -r requirements.txt && python main.py`로 바로 실행된다
- 2인 로컬 대전과 AI 대전이 동작한다
- 게임 로직(`board.py`, `ai.py`)은 pygame에 의존하지 않으며 pytest로 검증된다
- 이후 FastAPI/MCP 단계에서 `board.py`, `ai.py`를 수정 없이 import 할 수 있다

## 범위

포함:
- 15×15 판, 자유룰 (같은 색 5개 이상 연속 시 승리, 금수 없음)
- 모드: 2인 로컬 대전, AI 대전 (사람 = 흑, 선공)
- 무르기(`U`), 다시 시작(`R`), 메뉴로(`ESC`)
- 마지막 수 표시, 차례/결과 메시지

제외 (추후): 렌주룰 금수, 미니맥스 AI, 효과음, 저장/불러오기, 타이머

## 구조

```
omokgame/
├── omok/
│   ├── __init__.py
│   ├── board.py
│   ├── ai.py
│   └── game.py
├── tests/
│   ├── test_board.py
│   └── test_ai.py
├── main.py
├── requirements.txt   # pygame, pytest
└── README.md
```

의존 방향: `game.py → ai.py → board.py`. `board.py`, `ai.py`는 pygame을 import 하지 않는다.

## board.py

상수: `SIZE = 15`, `EMPTY = 0`, `BLACK = 1`, `WHITE = 2`

`class Board`:
- `grid: list[list[int]]` — `grid[r][c]`, 초기값 전부 `EMPTY`
- `history: list[tuple[int, int]]` — 착수 순서
- `turn: int` — 다음 착수 색. 시작은 `BLACK`
- `place(r, c) -> bool` — 범위 밖, 빈칸 아님, 이미 승부가 났으면 `False`. 성공 시 `grid` 갱신, `history` 추가, `turn` 교대, `True`
- `undo() -> bool` — `history`가 비면 `False`. 마지막 수 제거, `turn` 되돌림
- `winner() -> int` — 마지막 수 기준 4방향 `(0,1) (1,0) (1,1) (1,-1)`에서 양쪽 연속 개수 합(자신 포함)이 5 이상이면 그 색, 아니면 `EMPTY`. `history`가 비면 `EMPTY`
- `is_full() -> bool` — `len(history) == SIZE * SIZE`

## ai.py

`choose_move(board: Board, color: int) -> tuple[int, int]`
- `history`가 비면 중앙 `(7, 7)`
- 후보: 기존 돌로부터 체비셰프 거리 2 이내의 빈칸
- 각 후보 점수 = `evaluate(r, c, color) + evaluate(r, c, opponent)`. 판은 변경하지 않는다(가상 착수)
- `evaluate`: 4방향 각각, 해당 자리에 `color`를 두었다고 가정하고 연속 개수 `n`과 양 끝 빈칸 수 `open_ends(0~2)`를 구해 점수표로 합산

| 조건 | 점수 |
|---|---|
| n ≥ 5 | 100000 |
| n = 4, open 2 | 10000 |
| n = 4, open 1 | 1000 |
| n = 3, open 2 | 1000 |
| n = 3, open 1 | 100 |
| n = 2, open 2 | 100 |
| n = 2, open 1 | 10 |
| 그 외 | 1 |

- 공격 우선: 자신이 5목을 만들 수 있으면 상대 5목 차단보다 우선하도록 자신의 점수에 1.1배 가중치
- 최고 점수 후보 반환 (동점은 먼저 찾은 후보)

## game.py

- 창 크기: 판 15칸 × 40px + 여백, 상단 상태 표시줄
- 상태: `"menu"`, `"playing"`, `"over"` (문자열)
- 메뉴: "2인 대전", "AI 대전" 버튼 클릭으로 `mode` 설정 후 `"playing"`
- 착수: 클릭 픽셀 → 가장 가까운 교차점 `(r, c)` 반올림 변환 → `board.place`. 판 밖 클릭은 무시
- AI 모드: 사람 착수 성공 후 승부가 안 났으면 즉시 `choose_move`로 백 착수
- 매 착수 후 `winner()` 또는 `is_full()`이면 `"over"`
- `U`: 2인 모드 1수, AI 모드 2수 무르기 (`"over"`에서도 가능, 상태를 `"playing"`으로 복귀)
- `R`: 같은 모드로 새 `Board`. `ESC`: 메뉴로
- 60 FPS 루프: 이벤트 처리 → 그리기

## 오류 처리

- 잘못된 착수는 `place`가 `False`를 반환하고 화면은 변화 없음 (예외 없음)
- pygame 미설치 시 `main.py` import 단계의 기본 `ModuleNotFoundError`로 충분 (README에 설치 안내)

## 테스트 (pytest)

`test_board.py`:
- 가로/세로/↘/↗ 5목 승리
- 6목 승리 (자유룰)
- 4목은 `EMPTY`
- 범위 밖, 중복 착수 `False`
- `undo` 후 `grid`, `turn`, `history` 복원
- 승부 후 `place` `False`

`test_ai.py`:
- 빈 판 → `(7, 7)`
- 자신의 4연속이 있으면 5번째 자리로 승리
- 상대 열린 4연속을 막는 자리 선택
- 자신의 승리수와 상대 차단수가 동시에 있으면 승리수 선택

`game.py`는 수동 확인 (실행 후 두 모드 1판씩 플레이).

## Git

- 원격: https://github.com/jynlee/omokgame.git
- 커밋/푸시는 매번 사용자 확인 후 진행
- 커밋 메시지는 영어 (Conventional Commits)
