import math

import pygame
from pygame import gfxdraw

from omok.board import SIZE, BLACK, WHITE
from omok.layout import CELL, TOP, WIDTH, HEIGHT, cell_center
from omok.themes.common import rng, load_font, vgradient, radial, masked, aligned

STAR_POINTS = ((3, 3), (3, 11), (7, 7), (11, 3), (11, 11))
R = CELL // 2 - 2


def wave(x):
    return TOP - 7 + 4 * math.sin(x / 22)


def rotate(points, angle, cx, cy):
    ca, sa = math.cos(angle), math.sin(angle)
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in points]


def star(cx, cy, outer, inner, n, angle=-math.pi / 2):
    return [(cx + math.cos(angle + i * math.pi / n) * (outer if i % 2 == 0 else inner),
             cy + math.sin(angle + i * math.pi / n) * (outer if i % 2 == 0 else inner))
            for i in range(n * 2)]


def shadow(surf, c):
    pygame.draw.ellipse(surf, (90, 60, 25, 70), (c + 2 - R * .85, c + R * .72 - R * .28, R * 1.7, R * .56))


def conch_sprite():
    """흑: 하늘색 소라껍질. 왼쪽 나선 원 + 오른쪽 뾰족한 끝을 -0.55rad 회전."""
    size = int(R * 2.8)
    c = size / 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    shadow(surf, c)
    cx, rad, angle = -R * .32, R * .78, -.55
    body = [(R * 1.2, 0)] + [(cx + rad * math.cos(a), rad * math.sin(a))
                              for a in (-1.25 - i * (2 * math.pi - 2.5) / 24 for i in range(25))]
    body = rotate(body, angle, c, c)
    hl = rotate([(cx - R * .25, -R * .35)], angle, c, c)[0]
    fill = radial((size, size), hl, int(R * 1.4), [(0, (190, 232, 250, 255)), (1, (52, 128, 178, 255))])
    surf.blit(masked(fill, body), (0, 0))
    gfxdraw.aapolygon(surf, [(round(x), round(y)) for x, y in body], (30, 88, 130))
    spiral = [(cx + math.cos(t) * rad * .82 * (1 - t / (math.pi * 3.6)),
               math.sin(t) * rad * .82 * (1 - t / (math.pi * 3.6)))
              for t in (i * .15 for i in range(int(math.pi * 3.2 / .15) + 1))]
    pygame.draw.aalines(surf, (255, 255, 255), False, rotate(spiral, angle, c, c))
    for k in (-.35, 0, .35):
        pygame.draw.aaline(surf, (225, 242, 252), *rotate([(cx + rad * .75, k * rad), (R * 1.1, k * R * .08)], angle, c, c))
    return surf


def scallop_sprite():
    """백: 조개껍질. 아래 중심의 부채꼴 7골."""
    size = int(R * 2.8)
    c = size / 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    shadow(surf, c)
    by, big, a0, a1, n = R * .62, R * 1.45, -math.pi + .75, -.75, 7

    def edge(i, scale=1.0):
        a = a0 + (a1 - a0) * i / n
        return c + math.cos(a) * big * scale, c + by + math.sin(a) * big * scale

    outline = [(c, c + by), edge(0)]
    for i in range(1, n + 1):
        p0, p2 = edge(i - 1), edge(i)
        p1 = edge(i - .5, 1.12)
        for k in range(1, 7):
            t = k / 6
            outline.append(tuple((1 - t) ** 2 * a + 2 * (1 - t) * t * b + t * t * d for a, b, d in zip(p0, p1, p2)))
    fill = radial((size, size), (c - R * .3, c - R * .5), int(R * 1.5), [(0, (255, 247, 243, 255)), (1, (239, 159, 176, 255))])
    surf.blit(masked(fill, outline), (0, 0))
    gfxdraw.aapolygon(surf, [(round(x), round(y)) for x, y in outline], (197, 106, 128))
    for i in range(1, n):
        ex, ey = edge(i)
        pygame.draw.aaline(surf, (210, 130, 150), (c, c + by), (c + (ex - c) * .92, c + by + (ey - c - by) * .92))
    ear = [(c - R * .32, c + by - 1), (c + R * .32, c + by - 1), (c + R * .2, c + by + R * .22), (c - R * .2, c + by + R * .22)]
    pygame.draw.polygon(surf, (246, 195, 205), ear)
    gfxdraw.aapolygon(surf, [(round(x), round(y)) for x, y in ear], (197, 106, 128))
    return surf


def glow_sprites(levels=16):
    """더하기 합성용 금빛 원. 밝기 단계별로 미리 만들어 둔다 (돌을 가리지 않고 빛나게)."""
    rad = int(CELL * .95)
    base = radial((rad * 2, rad * 2), (rad, rad), rad, [(0, (255, 214, 80, 255)), (1, (0, 0, 0, 255))])
    out = []
    for i in range(levels):
        img = base.copy()
        k = round(255 * i / (levels - 1))
        img.fill((k, k, k), special_flags=pygame.BLEND_RGB_MULT)
        out.append(img)
    return out


class Sand:
    title = "모래사장"
    names = {BLACK: "소라(흑)", WHITE: "조개(백)"}
    ink = (70, 50, 25)
    text_color = (255, 255, 255)

    def __init__(self):
        self._bg = None
        self._sprites = {}
        self._text_cache = {}

    def background(self):
        if self._bg is None:
            self._bg = self._draw_background()
        return self._bg

    def _draw_background(self):
        bg = pygame.Surface((WIDTH, HEIGHT))
        vgradient(bg, (0, 0, WIDTH, HEIGHT), (244, 226, 184), (227, 196, 138))
        over = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        rnd = rng(7)
        for _ in range(6000):
            color = (150, 110, 55, 50) if rnd.random() < .5 else (255, 250, 235, 100)
            over.fill(color, (rnd.random() * WIDTH, rnd.random() * HEIGHT, 1, 1))
        for k in range(15):
            y0 = TOP + 14 + k * 33 + rnd.random() * 10
            pts = [(x, y0 + math.sin(x / 36 + k) * 4) for x in range(0, WIDTH + 8, 8)]
            pygame.draw.lines(over, (185, 145, 85, 50), False, pts, 2)
        bg.blit(over, (0, 0))
        for i in range(SIZE):
            for a, b in ((cell_center(i, 0), cell_center(i, SIZE - 1)), (cell_center(0, i), cell_center(SIZE - 1, i))):
                pygame.draw.line(bg, (115, 80, 38), a, b, 2)
                pygame.draw.line(bg, (255, 248, 225), (a[0] + 1, a[1] + 1), (b[0] + 1, b[1] + 1))
        for r, c in STAR_POINTS:
            x, y = cell_center(r, c)
            pygame.draw.ellipse(bg, (169, 128, 76), (x - 4, y - 3, 8, 6))
        sea = pygame.Surface((WIDTH, TOP + 4), pygame.SRCALPHA)
        vgradient(sea, (0, 0, WIDTH, TOP + 4), (43, 134, 168), (92, 195, 212))
        below = [(x, wave(x)) for x in range(0, WIDTH + 4, 4)] + [(WIDTH, TOP + 4), (0, TOP + 4)]
        pygame.draw.polygon(sea, (0, 0, 0, 0), below)
        bg.blit(sea, (0, 0))
        crest = [(x, wave(x)) for x in range(0, WIDTH + 4, 4)]
        pygame.draw.lines(bg, (255, 255, 255), False, crest, 3)
        return bg

    def _sprite(self, key, make):
        if key not in self._sprites:
            self._sprites[key] = make()
        return self._sprites[key]

    def stone(self, surf, x, y, color, seed):
        img = self._sprite(color, conch_sprite if color == BLACK else scallop_sprite)
        surf.blit(img, img.get_rect(center=(x, y)))

    def last_mark(self, surf, x, y):
        pts = [(round(px), round(py)) for px, py in star(x + R * .75, y - R * .7, 8, 3.6, 5, -math.pi / 2 + .3)]
        gfxdraw.filled_polygon(surf, pts, (255, 138, 61))
        gfxdraw.aapolygon(surf, pts, (201, 90, 26))

    def win_effect(self, surf, points, t):
        glows = self._sprite("glow", glow_sprites)
        level = .2 + .25 * (.5 + .5 * math.sin(t / 450))  # 은은하게 숨 쉬듯
        glow = glows[round(level * (len(glows) - 1))]
        for x, y in points:
            surf.blit(glow, glow.get_rect(center=(x, y)), special_flags=pygame.BLEND_RGB_ADD)
        (x0, y0), (x1, y1) = points[0], points[-1]
        rnd = rng(42)
        for _ in range(14):
            k = rnd.random() * 1.2 - .1
            sx = x0 + (x1 - x0) * k + (rnd.random() - .5) * 34
            sy = y0 + (y1 - y0) * k + (rnd.random() - .5) * 34
            size, phase, gold = 2 + rnd.random() * 3, rnd.random() * 6.28, rnd.random() < .5
            a = max(0.0, math.sin(t / 420 + phase))
            if a > .05:
                pts = [(round(px), round(py)) for px, py in star(sx, sy, size * a, size * a * .25, 4)]
                color = (255, 226, 120) if gold else (255, 255, 255)
                gfxdraw.filled_polygon(surf, pts, color)
                gfxdraw.aapolygon(surf, pts, color)

    def text(self, surf, s, size, pos, align="left", rough=1.0, color=None):
        color = color or self.text_color
        key = (s, size, color)
        if key not in self._text_cache:
            font = load_font("Jua-Regular.ttf", size)
            front = font.render(s, True, color)
            img = pygame.Surface((front.get_width() + 1, front.get_height() + 1), pygame.SRCALPHA)
            if color == self.text_color:  # 흰 글씨는 바다 위에서 잘 보이도록 그림자
                img.blit(font.render(s, True, (0, 60, 90)), (1, 1))
            img.blit(front, (0, 0))
            self._text_cache[key] = img
        img = self._text_cache[key]
        surf.blit(img, aligned(img, pos, align))
