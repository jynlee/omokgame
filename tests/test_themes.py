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
    pygame.display.init()
    pygame.font.init()
    pygame.display.set_mode((1, 1))
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


def test_chalk_text_cached():
    from omok.themes.chalk import Chalk
    theme, surf = Chalk(), pygame.Surface((WIDTH, HEIGHT))
    theme.text(surf, "흑 승리!", 34, (20, 30))
    theme.text(surf, "흑 승리!", 34, (20, 30))
    assert len(theme._text_cache) == 1


def test_three_themes_with_distinct_titles():
    assert [t.title for t in THEMES] == ["모래사장", "칠판", "칠판(분필 돌)"]
