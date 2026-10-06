import math

import pygame

from omok.board import SIZE, BLACK, WHITE
from omok.layout import CELL, WIDTH, HEIGHT, cell_center
from omok.themes.common import rng, load_font, radial, masked, aligned

STAR_POINTS = ((3, 3), (3, 11), (7, 7), (11, 3), (11, 11))
R = CELL // 2 - 2
CHALK = (238, 242, 232)


def chalk_line(surf, p1, p2, rnd, color, width, upto=1.0, alpha=(140, 230)):
    """흔들리고 군데군데 끊긴 분필선. surf는 SRCALPHA여야 마디별 투명도가 남는다."""
    (x1, y1), (x2, y2) = p1, p2
    length = math.hypot(x2 - x1, y2 - y1)
    steps = max(2, round(length / 9))
    nx, ny = -(y2 - y1) / length, (x2 - x1) / length
    for _ in range(2):
        px, py = x1, y1
        for i in range(1, int(steps * upto) + 1):
            t, j = i / steps, (rnd.random() - .5) * 1.4
            qx, qy = x1 + (x2 - x1) * t + nx * j, y1 + (y2 - y1) * t + ny * j
            if rnd.random() > .05:
                pygame.draw.line(surf, (*color, alpha[0] + int(rnd.random() * (alpha[1] - alpha[0]))), (px, py), (qx, qy), width)
            px, py = qx, qy


def circle_points(cx, cy, radius, n=48):
    return [(cx + math.cos(i * 2 * math.pi / n) * radius, cy + math.sin(i * 2 * math.pi / n) * radius) for i in range(n)]


def stone3d_sprite(black):
    size = R * 2 + 8
    c = size / 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surf, (0, 0, 0, 90), (c + 2, c + 2.5), R)
    stops = ([(0, (109, 109, 109, 255)), (.35, (29, 29, 29, 255)), (1, (0, 0, 0, 255))] if black else
             [(0, (255, 255, 255, 255)), (.6, (238, 238, 234, 255)), (1, (189, 189, 182, 255))])
    fill = radial((size, size), (c - R * .35, c - R * .4), int(R * 1.4), stops)
    surf.blit(masked(fill, circle_points(c, c, R)), (0, 0))
    return surf


class Chalk:
    title = "칠판"
    names = {BLACK: "흑", WHITE: "백"}
    ink = CHALK
    text_color = (244, 246, 238)
    mark_color = (232, 93, 117)
    win_color = (255, 156, 192)

    def __init__(self):
        self._bg = None
        self._sprites = {}
        self._text_cache = {}

    def background(self):
        if self._bg is None:
            self._bg = self._draw_background()
        return self._bg

    def _draw_background(self):
        rnd = rng(3)
        bg = pygame.Surface((WIDTH, HEIGHT))
        bg.fill((44, 74, 58))
        for _ in range(70):  # 지우개 얼룩
            x, y, rad = rnd.random() * WIDTH, rnd.random() * HEIGHT, int(30 + rnd.random() * 90)
            a = 6 + int(rnd.random() * 10)
            blob = radial((rad * 2, rad * 2), (rad, rad), rad, [(0, (230, 240, 230, a)), (1, (230, 240, 230, 0))])
            bg.blit(blob, (x - rad, y - rad))
        over = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for _ in range(4):  # 가로로 쓱 지운 자국
            y = 120 + rnd.random() * (HEIGHT - 240)
            a, b = (40 + rnd.random() * 80, y), (WIDTH - 40 - rnd.random() * 80, y + (rnd.random() - .5) * 30)
            pygame.draw.line(over, (235, 240, 230, 13), a, b, 26)
            for end in (a, b):  # 둥근 끝
                pygame.draw.circle(over, (235, 240, 230, 13), end, 13)
        for _ in range(2500):  # 분필 가루
            over.fill((240, 245, 235, int(rnd.random() * 18)), (rnd.random() * WIDTH, rnd.random() * HEIGHT, 1, 1))
        for i in range(SIZE):
            (a, b), (c, d) = cell_center(i, 0), cell_center(i, SIZE - 1)
            chalk_line(over, (a - 4 + rnd.random() * 3, b + (rnd.random() - .5) * 2),
                       (c + 4 - rnd.random() * 3, d + (rnd.random() - .5) * 2), rnd, CHALK, 1, alpha=(110, 200))
            (e, f), (h, k) = cell_center(0, i), cell_center(SIZE - 1, i)
            chalk_line(over, (e + (rnd.random() - .5) * 2, f - 4 + rnd.random() * 3),
                       (h + (rnd.random() - .5) * 2, k + 4 - rnd.random() * 3), rnd, CHALK, 1, alpha=(110, 200))
        for r, c in STAR_POINTS:
            pygame.draw.circle(over, (240, 244, 236, 217), cell_center(r, c), 3)
        bg.blit(over, (0, 0))
        pygame.draw.rect(bg, (124, 79, 43), (0, 0, WIDTH, HEIGHT), 12)
        pygame.draw.rect(bg, (91, 55, 25), (11, 11, WIDTH - 22, HEIGHT - 22), 2)
        return bg

    def stone(self, surf, x, y, color):
        if color not in self._sprites:
            self._sprites[color] = stone3d_sprite(color == BLACK)
        img = self._sprites[color]
        surf.blit(img, img.get_rect(center=(x, y)))

    def last_mark(self, surf, x, y):
        pygame.draw.circle(surf, self.mark_color, (x, y), 4, 2)

    def win_effect(self, surf, points, t):
        (x0, y0), (x1, y1) = points[0], points[-1]
        ex, ey = (x1 - x0) * .14, (y1 - y0) * .14
        p = min(1.0, (t % 3200) / 1300)
        layer = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        chalk_line(layer, (x0 - ex, y0 - ey), (x1 + ex, y1 + ey), rng(9), self.win_color, 5, p)
        surf.blit(layer, (0, 0))

    def text(self, surf, s, size, pos, align="left", rough=1.0, color=None):
        color = color or self.text_color
        size = round(size * 1.3)  # 손글씨 글꼴은 같은 크기에서 글자가 작게 나와 키운다
        key = (s, size, rough, color)
        if key not in self._text_cache:
            self._text_cache[key] = self._chalk_text(s, size, rough, color)
        img = self._text_cache[key]
        surf.blit(img, aligned(img, pos, align))

    def _chalk_text(self, s, size, rough, color):
        """1) 살짝 어긋나게 세 번 칠하기 2) 가로 결 따라 알파 지우기 3) 가루 뿌리기."""
        rnd = rng(hash((s, size)) & 0xFFFF)
        font = load_font("NanumPenScript-Regular.ttf", size)
        glyph = font.render(s, True, color)
        w, h = glyph.get_width() + 4, glyph.get_height() + 4
        img = pygame.Surface((w, h), pygame.SRCALPHA)
        ghost = glyph.copy()
        ghost.set_alpha(round(115 * rough))
        img.blit(ghost, (2.8, 1.3))
        img.blit(ghost, (1.4, 2.6))
        glyph.set_alpha(230)
        img.blit(glyph, (2, 2))
        for _ in range(int(w * h * .09 * rough)):
            rect = (rnd.random() * w, rnd.random() * h, 1 + rnd.random() * 3.5, 1)
            img.fill((0, 0, 0, 90 + int(rnd.random() * 165)), rect, special_flags=pygame.BLEND_RGBA_SUB)
        for _ in range(int(w * .5 * rough)):
            x, y = int(rnd.random() * w), int(h * .25 + rnd.random() * h * .6)
            if img.get_at((x, y)).a < 56:
                img.set_at((x, y), (*color, 56))
        return img
