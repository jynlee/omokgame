from omok.board import SIZE, EMPTY, BLACK, WHITE, DIRECTIONS

# (연속 개수, 열린 끝 수) -> 점수. 없는 조합은 1점
SCORES = {(5, 0): 100000, (5, 1): 100000, (5, 2): 100000,
          (4, 2): 10000, (4, 1): 1000, (3, 2): 1000,
          (3, 1): 100, (2, 2): 100, (2, 1): 10}


def line_score(grid, r, c, dr, dc, color):
    """(r, c)에 color를 둔다고 가정하고 한 방향의 연속 개수와 열린 끝으로 점수를 매긴다."""
    n, open_ends = 1, 0
    for sign in (1, -1):
        rr, cc = r + dr * sign, c + dc * sign
        while 0 <= rr < SIZE and 0 <= cc < SIZE and grid[rr][cc] == color:
            n += 1
            rr += dr * sign
            cc += dc * sign
        if 0 <= rr < SIZE and 0 <= cc < SIZE and grid[rr][cc] == EMPTY:
            open_ends += 1
    return SCORES.get((min(n, 5), open_ends), 1)


def evaluate(grid, r, c, color):
    return sum(line_score(grid, r, c, dr, dc, color) for dr, dc in DIRECTIONS)


def candidates(grid):
    """돌로부터 2칸 이내의 빈칸. 없으면 모든 빈칸."""
    empty = [(r, c) for r in range(SIZE) for c in range(SIZE) if grid[r][c] == EMPTY]
    near = [(r, c) for r, c in empty
            if any(grid[rr][cc] != EMPTY
                   for rr in range(max(0, r - 2), min(SIZE, r + 3))
                   for cc in range(max(0, c - 2), min(SIZE, c + 3)))]
    return near or empty


def choose_move(board, color):
    if not board.history:
        return SIZE // 2, SIZE // 2
    opponent = WHITE if color == BLACK else BLACK
    grid = board.grid
    # 공격 점수에 1.1배 가중치: 내 승리수가 상대 차단수보다 우선
    return max(candidates(grid),
               key=lambda p: 1.1 * evaluate(grid, *p, color) + evaluate(grid, *p, opponent))
