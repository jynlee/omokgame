# 테마와 AI 난이도 설계

- 날짜: 2026-10-06
- 선행: `docs/design/2026-10-06-omok-core-pygame-design.md` (코어 + Pygame, 구현 완료)
- 시안: 모래사장 / 칠판 + 입체돌 / 칠판 + 분필 낙서 돌 (사용자 확정)

## 목적

기본 도형으로 그린 화면을 테마가 있는 화면으로 바꾸고, AI 대전에 난이도 3단계를 추가한다.

성공 기준:
- 메뉴에서 테마 3종 중 하나를 고르면 메뉴, 게임 화면 전체에 적용된다
- 화면 문구가 한글로 표시된다 (글꼴 파일 포함)
- AI 대전에서 Easy / Normal / Hard를 고를 수 있고, 난이도 차이가 체감된다
- Hard의 한 수 계산은 1초 이내를 목표로 한다
- `board.py`, `ai.py`는 여전히 pygame에 의존하지 않는다

## 범위

포함: 테마 3종, 승리 5목 강조 효과, 한글 글꼴, 메뉴의 테마 선택, 난이도 선택 화면, Hard 계산 중 "생각 중..." 표시

제외 (추후): 마우스 위치 미리보기, 효과음, 설정 저장(테마는 실행 중에만 유지, 시작 시 모래사장)

---

## 1부. 테마

### 구조

```
assets/fonts/
  Jua-Regular.ttf, Jua-OFL.txt
  NanumPenScript-Regular.ttf, NanumPenScript-OFL.txt
omok/layout.py          CELL, MARGIN, TOP, WIDTH, HEIGHT, cell_center(r, c)
omok/themes/__init__.py THEMES = [Sand(), Chalk(), Chalk(doodle=True)]
omok/themes/common.py   rng(seed), load_font(file, size)
omok/themes/sand.py     class Sand
omok/themes/chalk.py    class Chalk
```

- 글꼴 출처: Google Fonts 공식 저장소 `github.com/google/fonts`의 `ofl/jua`, `ofl/nanumpenscript`. 둘 다 SIL OFL 1.1이며 라이선스 파일을 함께 둔다
- 글꼴 경로는 `omok` 패키지 기준 `../assets/fonts` (실행 위치와 무관)
- `layout.py`는 기존 `game.py`의 배치 상수와 `cell_center`를 옮긴 것. `game.py`는 이를 import 하므로 `from omok.game import CELL, MARGIN, TOP`는 계속 동작한다
- `rng(seed)`는 `random.Random(seed)`. 같은 시드면 같은 모양이 나와서 매 프레임 그려도 떨리지 않는다

### 테마 인터페이스

모든 테마는 아래 속성과 메서드를 가진다. `game.py`는 어떤 테마인지 모르고 이것만 호출한다.

| 이름 | 설명 |
|---|---|
| `title: str` | 메뉴 표시 이름: `"모래사장"`, `"칠판"`, `"칠판(분필 돌)"` |
| `names: dict[int, str]` | 상태 문구용 색 이름 |
| `background() -> Surface` | `WIDTH × HEIGHT` 배경 (격자, 화점, 상단 바 포함). 첫 호출 때 그려서 캐시 |
| `stone(surf, x, y, color, seed)` | 돌 하나. `seed`로 분필 돌의 모양을 고정 |
| `last_mark(surf, x, y)` | 마지막 수 표시 |
| `win_effect(surf, points, t)` | 승리 강조. `points`는 승리 칸들의 픽셀 좌표, `t`는 ms |
| `text(surf, s, size, pos, align="left", rough=1.0, color=None)` | 문구. `pos`는 기준점, `align`은 `"left"`/`"center"`/`"right"`, `color`가 없으면 테마 기본 글씨색 |
| `ink: tuple` | 메뉴 버튼 테두리, 글씨 색 |

### 테마별 내용 (시안 그대로)

**Sand (모래사장)**
- 배경: 모래색 그라데이션, 모래 알갱이 점, 물결 자국, 홈 파인 격자선(진한 선 + 밝은 선 1px 어긋남), 화점은 작은 조약돌, 상단은 바다 그라데이션과 흰 파도 선
- 돌: 흑 = 소라껍질(갈색, 나선 무늬), 백 = 조개껍질(분홍, 부채꼴 골)
- `names`: `{BLACK: "소라(흑)", WHITE: "조개(백)"}`
- 마지막 수: 돌 오른쪽 위에 작은 주황 불가사리
- 승리: 승리 칸마다 황금빛 원형 빛(더하기 합성이라 돌을 가리지 않고 빛나게 함)이 약 2초 주기로 밝아졌다 어두워지고, 선 주변 반짝이 30개가 각자 위상으로 깜빡임
- 글꼴: Jua, 흰색, 상단 바 위에 그림자. `rough` 무시

**Chalk (칠판), `doodle=False`**
- 배경: 짙은 초록, 지우개 자국(크고 옅은 흰 얼룩, 가로 붓질), 분필 가루 점, 흔들리고 군데군데 끊긴 분필 격자선, 분필 점 화점, 나무 테두리
- 돌: 광택과 그림자가 있는 입체 흑돌, 백돌
- `names`: `{BLACK: "흑", WHITE: "백"}`
- 마지막 수: 분홍 작은 원 테두리
- 승리: 분홍 분필 선이 승리 5목을 양 끝보다 조금 더 길게 약 1.3초에 걸쳐 그어지고, 3.2초 주기로 반복
- 글씨: Nanum Pen Script + 분필 질감 (아래)

**Chalk, `doodle=True` (칠판(분필 돌))**
- 배경, 글씨: Chalk와 같음
- 돌: 흑 = 분홍 분필, 백 = 파란 분필. 원 안을 빗금으로 칠하고 흔들리는 테두리를 두 번 그림
- `names`: `{BLACK: "분홍(흑)", WHITE: "파랑(백)"}`
- 마지막 수: 흰 분필 작은 원
- 승리 선: 노란 분필 (분홍 돌과 구분)

### 분필 글씨

1. 별도 Surface에 글자를 그리고, 1px 안팎으로 어긋난 위치에 반투명으로 두 번 더 그린다
2. 가로로 긴 작은 사각형들을 무작위로 지운다 (지우는 양 ∝ `rough`)
3. 옅은 가루 점을 흩뿌린다 (양 ∝ `rough`)
4. 결과를 `(s, size, rough)` 키로 캐시한다

- 승리/차례 문구: `rough=1.0`. 도움말: `rough=0.3` (가독성)

### 화면 문구

> 두 글꼴에 `·`, `…`, `◀`, `▶` 글리프가 없어 `|`, `...`, 도형 삼각형으로 대체한다

| 상황 | 문구 |
|---|---|
| 차례 | `"{names[turn]} 차례"` |
| 승리 | `"{names[winner]} 승리!"` |
| 무승부 | `"무승부"` |
| AI 계산 중 | `"생각 중..."` |
| 도움말 | `"U 무르기 \| R 다시 \| ESC 메뉴"` |
| 메뉴 버튼 | `"2인 대전"`, `"AI 대전"` |
| 테마 선택 | `{title}` 양옆에 도형으로 그린 ◀ ▶ 삼각형 버튼 |
| 난이도 버튼 | `"Easy"`, `"Normal"`, `"Hard"`, `"뒤로"` |

### 화면 흐름

- `menu`: 제목 `"오목"`, 버튼 `"2인 대전"` `"AI 대전"`, 테마 선택 줄. ◀ ▶ 클릭 또는 ←/→ 키로 테마를 순환하고 배경이 즉시 바뀐다
- `"AI 대전"` → `difficulty`: Easy / Normal / Hard / 뒤로. ESC도 뒤로
- `playing`, `over`: 기존과 동일. 그리기는 현재 테마로
- AI 모드에서 사람 착수 후 승부가 안 났으면, 먼저 `"생각 중..."` 상태로 한 프레임을 그린 다음 AI 수를 계산한다

### 승리 칸

`Board.winning_line() -> list[tuple[int, int]]`
- 승자가 없으면 `[]`
- 있으면 마지막 수를 지나는 연속 칸 전부(6목이면 6칸)를 한쪽 끝에서 다른 끝 순서로
- 승리 방향이 여러 개면 `DIRECTIONS` 순서상 처음 찾은 방향

---

## 2부. AI 난이도

`choose_move(board, color, level="normal", rand=None) -> tuple[int, int]`
- `level`: `"easy"`, `"normal"`, `"hard"`. 기본값 `"normal"`이라 기존 호출과 테스트는 그대로
- `rand`: `random.Random` 인스턴스 (테스트에서 시드 고정용). `None`이면 모듈 기본 난수
- 판(`board.grid`)을 변경하지 않는다. Hard는 복사본에서 탐색

공통 규칙 **필수 수**: 자신이 두면 5목이 되는 칸이 있으면 그 칸, 없고 상대가 두면 5목이 되는 칸이 있으면 그 칸. 모든 난이도가 이 규칙을 먼저 적용한다.

| 난이도 | 동작 |
|---|---|
| Normal | 현재 AI 그대로 (`1.1 × 공격 + 수비` 최고점) |
| Easy | 필수 수가 없으면 점수 상위 3개 후보 중 하나를 `rand`로 균등 선택 |
| Hard | 필수 수가 없으면 알파베타 가지치기 negamax, 깊이 5 (AI → 상대 → AI → 상대 → AI) |

### Hard 탐색

- 각 단계 후보: 휴리스틱 점수 상위 `K = 10`개, 점수 내림차순으로 탐색 (가지치기 효율)
- 착수로 5목이 되면 즉시 승리 값 `10**9 + 남은 깊이` (더 빠른 승리 선호)
- 말단 평가 (차례인 쪽 관점): `1.5 × patterns(차례) - patterns(상대)`. `patterns(c)`는 판 위 `c`의 연속 구간(2개 이상)마다 `(길이, 열린 끝)`을 기존 점수표로 매겨 합한 값. 1.5는 다음 수를 둘 수 있는 쪽의 주도권 가중치

> 설계 변경 근거 (2026-10-06 시제품 실험): 깊이 3 + "후보 칸 최고 점수" 말단 평가는 Normal에게 흑/백 모두 패배. 깊이 5 + 판 패턴 평가는 Normal에게 흑(21수), 백(28수) 모두 승리, 한 수 최대 약 1.1초

---

## 테스트

`test_board.py` 추가:
- `winning_line`: 가로 5칸, ↘ 대각선 5칸 순서, 6목이면 6칸, 승부 전 `[]`

`test_ai.py` 추가:
- Easy: 시드 여러 개에서 자신의 5목 완성 칸을 둔다. 상대 5목 차단 칸을 둔다
- Easy: 필수 수가 없는 판에서 시드에 따라 서로 다른 수가 2개 이상 나온다
- Hard: 빈 판에서 Hard 대 Normal로 끝까지 대국하면 Hard가 흑일 때도 백일 때도 이긴다 (둘 다 결정적이라 재현 가능). 같은 대국 중 Hard의 한 수 계산 최대 시간이 2초 미만 (1초 목표, 느린 PC 여유)
- 필수 수: 상대 5목 차단 칸을 Hard도 둔다
- Hard, Easy 모두 `board.grid`가 호출 전후로 같다

`test_themes.py` (`SDL_VIDEODRIVER=dummy`):
- 세 테마 각각 `background()`가 `(WIDTH, HEIGHT)` Surface를 반환하고, 두 번째 호출은 같은 객체(캐시)
- 각 테마로 `stone`(흑/백), `last_mark`, `win_effect`(t=0, 1000), `text`(left/center/right)가 오류 없이 그려진다
- Chalk `text`: 같은 인자 두 번 호출 시 내부 캐시 크기가 1만 늘어난다

수동 확인: 테마 3종 × 메뉴/게임/승리 화면, 난이도 3종 각각 한 판, Hard 응답 시간 체감
