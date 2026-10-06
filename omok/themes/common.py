import functools
import random
from pathlib import Path

import pygame

FONT_DIR = Path(__file__).resolve().parents[2] / "assets" / "fonts"


def rng(seed):
    """같은 시드면 같은 무늬: 매 프레임 그려도 모양이 떨리지 않는다."""
    return random.Random(seed)


@functools.cache
def load_font(file, size):
    pygame.font.init()
    return pygame.font.Font(FONT_DIR / file, size)


def lerp(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def vgradient(surf, rect, top, bottom):
    """rect 안을 위→아래 색 그라데이션으로 채운다."""
    x, y, w, h = rect
    for i in range(h):
        pygame.draw.line(surf, lerp(top, bottom, i / max(1, h - 1)), (x, y + i), (x + w - 1, y + i))


def radial(size, center, radius, stops):
    """size 크기 SRCALPHA Surface에 center 기준 방사형 그라데이션. stops = [(t, rgba), ...]"""
    surf = pygame.Surface(size, pygame.SRCALPHA)
    surf.fill(stops[-1][1])  # 반지름 밖은 마지막 색 (모서리가 비지 않게)
    for rad in range(radius, 0, -1):
        t = rad / radius
        for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
            if t0 <= t <= t1:
                color = lerp(c0, c1, (t - t0) / ((t1 - t0) or 1))
                break
        else:
            color = stops[-1][1]
        pygame.draw.circle(surf, color, center, rad)
    return surf


def masked(fill, points):
    """fill Surface에서 points 다각형 바깥을 투명하게."""
    mask = pygame.Surface(fill.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(mask, (255, 255, 255, 255), points)
    out = fill.copy()
    out.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return out


def aligned(img, pos, align):
    """pos = (x, 세로 중앙 y). align에 따라 왼쪽/가운데/오른쪽 기준."""
    rect = img.get_rect()
    setattr(rect, {"left": "midleft", "center": "center", "right": "midright"}[align], pos)
    return rect
