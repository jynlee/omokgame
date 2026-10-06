"""웹 빌드: 게임 파일만 dist/omokgame 으로 모아 pygbag 으로 빌드한다.

    python tools/build_web.py           # dist/omokgame/build/web 에 웹 파일 생성
    python tools/build_web.py --serve   # 빌드 후 http://localhost:8000 으로 미리보기
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist" / "omokgame"
GAME_FILES = ["main.py", "omok", "assets"]  # 테스트, 문서, 가상환경은 웹 파일에 넣지 않는다


def stage():
    shutil.rmtree(DIST, ignore_errors=True)
    DIST.mkdir(parents=True)
    for name in GAME_FILES:
        src = ROOT / name
        if src.is_dir():
            shutil.copytree(src, DIST / name, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy2(src, DIST / name)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--serve", action="store_true", help="빌드 후 http://localhost:8000 에서 미리보기")
    args = parser.parse_args()
    stage()
    # --ume_block 0: 소리를 쓰지 않으므로 "클릭해서 시작" 단계 없이 바로 시작
    cmd = [sys.executable, "-m", "pygbag", "--title", "Omok", "--ume_block", "0"]
    if not args.serve:
        cmd.append("--build")
    subprocess.run([*cmd, str(DIST)], check=True)


if __name__ == "__main__":
    main()
