import random

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


LEVELS = ("easy", "normal", "hard")

# Hard 탐색: 단계별 후보 수, 읽는 수, 승리 값, 차례인 쪽 주도권 가중치
K, DEPTH, WIN, INITIATIVE = 10, 5, 10**9, 1.5
YIELD_EVERY = 50  # 탐색 노드 이만큼마다 화면에 차례를 넘긴다 (한 번에 약 30ms, 웹은 2~3배)


def other(color):
    return WHITE if color == BLACK else BLACK


def makes_five(grid, r, c, color):
    return any(line_score(grid, r, c, dr, dc, color) >= 100000 for dr, dc in DIRECTIONS)


def forced_move(grid, color):
    """내가 5목을 만드는 칸, 없으면 상대의 5목을 막는 칸, 없으면 None."""
    cands = candidates(grid)
    for who in (color, other(color)):
        for r, c in cands:
            if makes_five(grid, r, c, who):
                return r, c
    return None


def ranked(grid, color):
    """후보를 휴리스틱 점수 내림차순으로. 공격에 1.1배 가중치(내 승리수 우선)."""
    opp = other(color)
    return sorted(candidates(grid),
                  key=lambda p: -(1.1 * evaluate(grid, *p, color) + evaluate(grid, *p, opp)))


def patterns(grid, color):
    """color 돌의 연속 구간(2개 이상)마다 (길이, 열린 끝)을 SCORES로 매겨 합산."""
    total = 0
    for r in range(SIZE):
        for c in range(SIZE):
            if grid[r][c] != color:
                continue
            for dr, dc in DIRECTIONS:
                pr, pc = r - dr, c - dc
                if 0 <= pr < SIZE and 0 <= pc < SIZE and grid[pr][pc] == color:
                    continue  # 구간의 시작점에서만 센다
                n, rr, cc = 0, r, c
                while 0 <= rr < SIZE and 0 <= cc < SIZE and grid[rr][cc] == color:
                    n, rr, cc = n + 1, rr + dr, cc + dc
                if n >= 2:
                    open_ends = sum(0 <= y < SIZE and 0 <= x < SIZE and grid[y][x] == EMPTY
                                    for y, x in ((rr, cc), (pr, pc)))
                    total += SCORES.get((min(n, 5), open_ends), 0)
    return total


def negamax_steps(grid, color, depth, alpha, beta, counter):
    """알파베타 negamax. 값은 차례인 color 관점. 노드 YIELD_EVERY개마다 멈춰 화면에 차례를 넘긴다."""
    counter[0] += 1
    if counter[0] % YIELD_EVERY == 0:
        yield
    opp = other(color)
    if depth == 0:
        return INITIATIVE * patterns(grid, color) - patterns(grid, opp)
    best = -WIN * 10
    for r, c in ranked(grid, color)[:K]:
        if makes_five(grid, r, c, color):
            return WIN + depth  # 빨리 이길수록 큰 값
        grid[r][c] = color
        value = -(yield from negamax_steps(grid, opp, depth - 1, -beta, -alpha, counter))
        grid[r][c] = EMPTY
        best, alpha = max(best, value), max(alpha, value)
        if alpha >= beta:
            break
    return best


def search_steps(board, color):
    grid = [row[:] for row in board.grid]  # 원본 판은 건드리지 않는다
    opp = other(color)
    counter = [0]
    best, move, alpha = -WIN * 10, None, -WIN * 10
    for r, c in ranked(grid, color)[:K]:
        grid[r][c] = color
        value = -(yield from negamax_steps(grid, opp, DEPTH - 1, -WIN * 10, -alpha, counter))
        grid[r][c] = EMPTY
        if value > best:
            best, move = value, (r, c)
        alpha = max(alpha, value)
    return move


def move_steps(board, color, level="normal", rand=None):
    """둘 수를 계산하는 제너레이터. Hard만 중간중간 yield하고, 끝나면 (r, c)를 return."""
    if not board.history:
        return SIZE // 2, SIZE // 2
    forced = forced_move(board.grid, color)
    if forced:
        return forced
    if level == "easy":
        return (rand or random).choice(ranked(board.grid, color)[:3])
    if level == "hard":
        return (yield from search_steps(board, color))
    return ranked(board.grid, color)[0]


def choose_move(board, color, level="normal", rand=None):
    steps = move_steps(board, color, level, rand)
    while True:
        try:
            next(steps)
        except StopIteration as done:
            return done.value
