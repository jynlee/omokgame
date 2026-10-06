SIZE = 15
EMPTY, BLACK, WHITE = 0, 1, 2
DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))


class Board:
    def __init__(self):
        self.grid = [[EMPTY] * SIZE for _ in range(SIZE)]
        self.history = []
        self.turn = BLACK

    def place(self, r, c):
        if not (0 <= r < SIZE and 0 <= c < SIZE):
            return False
        if self.grid[r][c] != EMPTY or self.winner() != EMPTY:
            return False
        self.grid[r][c] = self.turn
        self.history.append((r, c))
        self.turn = WHITE if self.turn == BLACK else BLACK
        return True

    def undo(self):
        if not self.history:
            return False
        r, c = self.history.pop()
        self.turn = self.grid[r][c]
        self.grid[r][c] = EMPTY
        return True

    def winner(self):
        """마지막 수 기준으로 4방향을 세어 5개 이상이면 그 색을 반환."""
        if not self.history:
            return EMPTY
        r, c = self.history[-1]
        color = self.grid[r][c]
        for dr, dc in DIRECTIONS:
            count = 1
            for sign in (1, -1):
                rr, cc = r + dr * sign, c + dc * sign
                while 0 <= rr < SIZE and 0 <= cc < SIZE and self.grid[rr][cc] == color:
                    count += 1
                    rr += dr * sign
                    cc += dc * sign
            if count >= 5:
                return color
        return EMPTY

    def is_full(self):
        return len(self.history) == SIZE * SIZE
