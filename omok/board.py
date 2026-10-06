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

    def _run(self, r, c, dr, dc):
        """(r, c)를 지나는 같은 색 연속 칸을 음의 방향 끝부터 순서대로."""
        color = self.grid[r][c]
        while 0 <= r - dr < SIZE and 0 <= c - dc < SIZE and self.grid[r - dr][c - dc] == color:
            r, c = r - dr, c - dc
        cells = []
        while 0 <= r < SIZE and 0 <= c < SIZE and self.grid[r][c] == color:
            cells.append((r, c))
            r, c = r + dr, c + dc
        return cells

    def winning_line(self):
        """마지막 수를 지나는 5개 이상 연속 칸. 승부 전이면 []."""
        if not self.history:
            return []
        r, c = self.history[-1]
        if self.grid[r][c] == EMPTY:
            return []
        for dr, dc in DIRECTIONS:
            cells = self._run(r, c, dr, dc)
            if len(cells) >= 5:
                return cells
        return []

    def winner(self):
        line = self.winning_line()
        return self.grid[line[0][0]][line[0][1]] if line else EMPTY

    def is_full(self):
        return len(self.history) == SIZE * SIZE
