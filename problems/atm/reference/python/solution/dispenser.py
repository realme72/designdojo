from __future__ import annotations

from contract import NoteBundle


class Dispenser:
    """Note cassettes. Finds exact amounts with the fewest notes (ties: higher notes)."""

    def __init__(self, notes: dict[int, int]):
        self.notes = dict(notes)

    def total(self) -> int:
        return sum(v * c for v, c in self.notes.items())

    def plan(self, amount: int) -> dict[int, int] | None:
        values = sorted((v for v, c in self.notes.items() if c > 0), reverse=True)
        best: dict[int, int] | None = None
        best_n = None

        def go(i: int, remaining: int, picked: dict[int, int], n: int) -> None:
            nonlocal best, best_n
            if remaining == 0:
                if best_n is None or n < best_n:
                    best, best_n = dict(picked), n
                return
            if i == len(values) or (best_n is not None and n >= best_n):
                return
            v = values[i]
            for k in range(min(self.notes[v], remaining // v), -1, -1):
                if k:
                    picked[v] = k
                go(i + 1, remaining - k * v, picked, n + k)
                picked.pop(v, None)

        go(0, amount, {}, 0)
        return best

    def take(self, plan: dict[int, int]) -> list[NoteBundle]:
        for v, k in plan.items():
            self.notes[v] -= k
        return [NoteBundle(v, k) for v, k in sorted(plan.items(), reverse=True)]
