from omok.board import SIZE

CELL, MARGIN, TOP = 40, 40, 60
WIDTH = MARGIN * 2 + CELL * (SIZE - 1)
HEIGHT = TOP + WIDTH


def cell_center(r, c):
    return MARGIN + c * CELL, TOP + MARGIN + r * CELL
