# 웹 빌드 설계

- 날짜: 2026-10-06
- 선행: `docs/design/2026-10-06-themes-and-difficulty-design.md` (테마, 난이도, 구현 완료)
- 브랜치: `feat/web-build`

## 목적

포트폴리오 방문자가 설치 없이 링크 하나로 플레이할 수 있게 한다.

성공 기준:
- `https://jynlee.github.io/omokgame/`을 열면 로딩 후 메뉴가 나오고 클릭(터치)으로 플레이할 수 있다
- 테마 2종, 한글 글꼴, 난이도 3단계가 웹에서도 동작한다
- Hard가 계산하는 동안에도 화면("생각 중" 애니메이션, 승리 효과)이 멈추지 않는다
- 휴대폰에서도 무르기, 다시 시작, 메뉴로 가기를 할 수 있다
- 데스크톱 실행(`python main.py`)과 기존 테스트는 그대로 동작한다
- `main`에 머지하면 테스트 → 빌드 → 배포가 자동으로 진행되고, 테스트가 실패하면 배포하지 않는다

## 범위

포함: 비동기 게임 루프, Hard 탐색 분할 실행, 상단 화면 버튼, pygbag 빌드 스크립트, GitHub Actions 테스트·배포, README 플레이 링크

제외 (추후): 휴대폰 세로 비율 전용 레이아웃, 오프라인 실행(PWA), 효과음

---

## 1. 비동기 게임 루프

- `omok/game.py`의 `run()`을 `async def main()`으로 바꾸고, 매 프레임 끝에 `await asyncio.sleep(0)`
- `main.py`:

```python
import asyncio

from omok.game import main

asyncio.run(main())
```

- pygbag은 `main.py`의 `asyncio.run(main())`과 프레임마다의 `await asyncio.sleep(0)`을 요구한다. 데스크톱에서는 일반 asyncio로 똑같이 동작한다

## 2. Hard 탐색 분할 실행

### ai.py

| 이름 | 설명 |
|---|---|
| `YIELD_EVERY = 200` | 탐색 노드(negamax 호출) 200개마다 한 번 멈춘다 |
| `move_steps(board, color, level="normal", rand=None)` | 제너레이터. 계산 중간중간 `yield`(값 없음)하고, 끝나면 `return (r, c)` |
| `choose_move(board, color, level="normal", rand=None)` | 기존과 같은 시그니처와 결과. 내부에서 `move_steps`를 끝까지 돌려 값을 반환 |

- Easy, Normal, 빈 판, 필수 수는 `yield` 없이 바로 `return`
- Hard는 기존 `search`/`negamax`를 `yield from`으로 이어지는 제너레이터로 바꾼다. 노드 카운터는 탐색 한 번 동안 공유한다
- 탐색 순서와 평가식은 바꾸지 않으므로 결과는 기존 Hard와 같다

### game.py

`advance(steps, budget_ms) -> tuple[bool, object]`
- `steps`를 `budget_ms` 동안 `next()`로 진행한다. 최소 1번은 진행한다
- 끝나면 `(True, 결과)`, 시간이 다 되면 `(False, None)`

AI 차례 흐름:
1. 사람 착수 후 AI 모드이고 진행 중이면 `ai_steps = move_steps(board, WHITE, level)`, `ai_move = None`, 최소 고민 시각 `ai_due` 설정 (기존 0.6~1.2초 유지)
2. 매 프레임 그리기를 마친 뒤 `ai_move`가 없으면 `advance(ai_steps, 12)`
3. `ai_move`가 정해지고 `ai_due`가 지나면 착수
4. 무르기, 다시, 메뉴(키 또는 버튼)를 누르면 진행 중인 계산을 버린다

- 계산하는 동안 들어온 클릭은 기존처럼 돌을 놓지 않는다(`ai_pending` 중 착수 무시). 화면 버튼은 계산 중에도 누를 수 있다

## 3. 상단 화면 버튼

- 기존 도움말 문구(`"U 무르기 | R 다시 | ESC 메뉴"`)를 버튼 3개로 대체한다: `"무르기"`, `"다시"`, `"메뉴"`
- 크기 64×30, 간격 8px, 오른쪽 끝을 `WIDTH - 16`에 맞추고 세로 중심 `TOP // 2 - 4` (모래사장 파도 위)
- 그리기: 테마 `text_color`로 2px 둥근 테두리(반지름 8), 글자 크기 18, `rough=0.3`, 가운데 정렬
- `playing`, `over` 상태에서만 보이고 동작한다. 동작은 각각 `U`, `R`, `ESC` 키와 같다 (키보드 단축키 유지)
- `bar_buttons() -> dict[str, pygame.Rect]`로 위치를 한곳에서 정한다

## 4. 웹 빌드

### tools/build_web.py

데스크톱(Windows, Linux)과 CI가 같은 방법으로 빌드하도록 하는 스크립트 하나.

```
python tools/build_web.py           # dist/omokgame/build/web 에 웹 파일 생성
python tools/build_web.py --serve   # 빌드 후 http://localhost:8000 으로 미리보기
```

- `dist/omokgame/`을 비우고 `main.py`, `omok/`, `assets/`만 복사한다 (테스트, 문서, 가상환경 제외)
- `python -m pygbag`을 실행한다. `--serve`가 없으면 `--build`(빌드만), 있으면 서버 실행
- `dist/`는 `.gitignore`에 추가
- pygbag은 개발용 도구라 `requirements.txt`에 넣지 않고 `requirements-dev.txt`에 `pygbag==0.9.3`으로 고정

## 5. GitHub Actions

`.github/workflows/pages.yml`

| 트리거 | 실행 |
|---|---|
| `pull_request` (main 대상) | 테스트, 빌드 |
| `push` (main) | 테스트, 빌드, 배포 |
| `workflow_dispatch` | 테스트, 빌드, 배포 (수동 재배포) |

- `test` 잡: Python 3.12, `pip install -r requirements.txt`, `SDL_VIDEODRIVER=dummy python -m pytest`
- `build` 잡 (`test` 성공 후): `pip install -r requirements-dev.txt`, `python tools/build_web.py`, `actions/upload-pages-artifact`로 `dist/omokgame/build/web` 업로드
- `deploy` 잡 (`build` 성공 후, `pull_request`가 아닐 때): `actions/deploy-pages`. 권한 `pages: write`, `id-token: write`
- 사용자 1회 설정: 저장소 Settings → Pages → Source를 "GitHub Actions"로

## 6. README

- 맨 위 줄을 `> 🎮 **브라우저에서 플레이**: https://jynlee.github.io/omokgame/`으로 교체 (배포 확인 후)
- 테스트 배지 추가: 워크플로 상태 배지
- 조작법 표에 화면 버튼 추가, "웹 빌드" 절 추가 (`requirements-dev.txt` 설치, `tools/build_web.py --serve`)

---

## 테스트

`test_ai.py` 추가:
- Hard `move_steps`가 중반 판에서 1번 이상 `yield`하고, 끝까지 돌린 결과가 `choose_move(..., "hard")`와 같다
- Easy, Normal `move_steps`는 `yield` 없이 바로 끝난다

`test_game.py` 추가:
- `advance`: 예산 0ms여도 최소 1번 진행하고, 반복 호출하면 `(True, 결과)`로 끝난다
- `bar_buttons`: 세 버튼이 서로 겹치지 않고, 모두 `y < TOP`이며, 각 버튼 중심을 `pixel_to_cell`에 넣으면 `None`

기존 45개는 그대로 통과해야 한다 (Hard 대 Normal 대국 포함, 한 수 2초 미만).

수동 확인:
- `python tools/build_web.py --serve`로 브라우저에서 메뉴 → 두 테마 → 난이도별 한 판, Hard 계산 중 애니메이션이 멈추지 않는지
- 배포 후 실제 링크를 PC와 휴대폰으로 확인, 화면 버튼 동작
