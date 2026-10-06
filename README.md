# Omok (오목)

Python과 pygame으로 만든 15×15 오목 게임입니다. 2인 대전과 난이도 3단계 AI 대전을 지원하고, 모래사장과 칠판 테마를 고를 수 있습니다.

> 🎮 **브라우저에서 플레이**: 준비 중 (웹 빌드 작업 예정)

| 모래사장 | 칠판 |
|---|---|
| ![모래사장 테마](docs/screenshots/sand.png) | ![칠판 테마](docs/screenshots/chalk.png) |

## 기능

- **2인 대전**: 한 화면에서 번갈아 둡니다
- **AI 대전**: Easy / Normal / Hard. 사람이 흑(선공)입니다
- **테마 2종**: 모래사장(소라와 조개), 칠판(입체 바둑돌)
- **승리 강조**: 완성된 5목에 금빛 반짝임 또는 분필 선 애니메이션
- **무르기, 다시 시작**: AI 대전에서는 사람 차례로 돌아갈 때까지 무릅니다
- **규칙**: 자유룰. 같은 색 5개 이상 연속이면 승리합니다 (6목 포함, 금수 없음)

## 실행

Python 3.12 이상이 필요합니다.

```bash
git clone https://github.com/jynlee/omokgame.git
cd omokgame
python -m venv .venv
.venv/Scripts/activate          # macOS, Linux: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## 조작법

| 입력 | 동작 |
|---|---|
| 마우스 클릭 | 교차점에 돌 놓기, 메뉴 버튼 선택 |
| ← / → (메뉴) | 테마 바꾸기 |
| U | 무르기 |
| R | 다시 시작 |
| ESC | 메뉴로 |

## 테스트

```bash
python -m pytest
```

규칙, AI, 테마 그리기, 화면 좌표 변환을 검증하는 테스트 45개가 있습니다. 그중 하나는 Hard AI와 Normal AI를 실제로 끝까지 대국시켜, Hard가 흑과 백 모두에서 이기는지 확인합니다.

## 구조

```
omok/
├── board.py        판 상태, 착수, 무르기, 승리 판정 (pygame 의존 없음)
├── ai.py           난이도별 AI (pygame 의존 없음)
├── layout.py       화면 배치 상수
├── game.py         pygame 화면, 입력, 게임 흐름
└── themes/
    ├── common.py   그라데이션, 글꼴 로딩 등 공통 도구
    ├── sand.py     모래사장 테마
    └── chalk.py    칠판 테마
assets/fonts/       Jua, Nanum Pen Script (SIL OFL 1.1)
tests/              pytest 테스트
docs/               설계 문서와 구현 계획
```

게임 규칙과 AI는 화면 코드와 분리되어 있어, 화면 없이 테스트할 수 있고 다른 인터페이스(웹 API 등)에서도 그대로 쓸 수 있습니다. 모든 테마는 같은 메서드(`background`, `stone`, `last_mark`, `win_effect`, `text`)를 가지므로 `game.py`는 어떤 테마인지 모른 채 그립니다. 그림은 이미지 파일 없이 코드로 그립니다.

## AI는 어떻게 두나요

**후보 칸**: 이미 놓인 돌에서 2칸 이내의 빈칸만 봅니다.

**점수 매기기**: 후보 칸에 돌을 놓았다고 가정하고, 4방향 각각에서 연속 개수와 양 끝이 열려 있는지를 봅니다.

| 패턴 | 점수 |
|---|---|
| 5목 | 100000 |
| 열린 4 | 10000 |
| 막힌 4, 열린 3 | 1000 |
| 막힌 3, 열린 2 | 100 |
| 막힌 2 | 10 |

칸의 점수는 `1.1 × 공격 점수 + 수비 점수`입니다. 공격에 가중치를 둬서 이길 수 있을 때는 막기보다 이기는 수를 둡니다.

**난이도**

- 모든 난이도는 먼저 **필수 수**를 확인합니다. 바로 5목을 만들 수 있으면 완성하고, 상대가 5목을 만들 수 있으면 막습니다.
- **Easy**: 점수 상위 3개 후보 중 하나를 무작위로 고릅니다.
- **Normal**: 점수가 가장 높은 칸에 둡니다.
- **Hard**: 알파베타 가지치기를 쓴 negamax로 5수 앞까지 읽습니다. 각 단계에서 점수 상위 10개 후보만 살펴보고, 마지막에는 판 위의 연속 패턴 점수로 형세를 평가합니다. 한 수 계산은 보통 1초 이내이고, 복잡한 국면에서는 2~3초까지 걸립니다.

처음에는 Hard를 3수 앞까지 읽게 설계했지만, 실제로 대국시켜 보니 Normal에게 졌습니다. 평가 방식을 바꾸고 5수 앞까지 읽게 해서 흑과 백 모두에서 이기도록 고쳤습니다. 과정은 `docs/design/`에 정리해 두었습니다.

## 글꼴 라이선스

[Jua](https://fonts.google.com/specimen/Jua), [Nanum Pen Script](https://fonts.google.com/specimen/Nanum+Pen+Script)는 SIL Open Font License 1.1을 따릅니다. 라이선스 전문은 `assets/fonts/`에 있습니다.

## 앞으로 할 일

- 웹 빌드(pygbag)와 GitHub Pages 배포로 브라우저에서 바로 플레이
- FastAPI로 게임 API 제공
- MCP 서버로 LLM이 오목을 두게 하기
