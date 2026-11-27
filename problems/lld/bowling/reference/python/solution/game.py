from __future__ import annotations

from contract import BowlingGame, GameOver, InvalidRoll

PINS = 10
FRAMES = 10


class Game(BowlingGame):
    """Rolls are the source of truth; frames are derived by walking them."""

    def __init__(self):
        self._rolls: list[int] = []

    # ---- frame walk ----
    def _frames(self) -> list[list[int]]:
        """Split rolls into frames; the 10th frame keeps its bonus rolls."""
        frames, i = [], 0
        while i < len(self._rolls) and len(frames) < FRAMES - 1:
            if self._rolls[i] == PINS:
                frames.append([PINS])
                i += 1
            else:
                frames.append(self._rolls[i:i + 2])
                i += 2
        if i < len(self._rolls):
            frames.append(self._rolls[i:])
        return frames

    def _standing_tenth(self, tenth: list[int]) -> int:
        """Pins standing for the next roll of the 10th frame (reset after strikes/spares)."""
        standing = PINS
        for k, r in enumerate(tenth):
            standing -= r
            spare_here = k == 1 and tenth[0] != PINS and tenth[0] + r == PINS
            if standing == 0 or spare_here:
                standing = PINS
        return standing

    def _tenth_done(self, tenth: list[int]) -> bool:
        if len(tenth) < 2:
            return False
        bonus = tenth[0] == PINS or tenth[0] + tenth[1] == PINS
        return len(tenth) == (3 if bonus else 2)

    def current_frame(self) -> int:
        f = self._frames()
        if not f:
            return 1
        if len(f) == FRAMES:
            return FRAMES
        last = f[-1]
        return len(f) + 1 if last == [PINS] or len(last) == 2 else len(f)

    def is_over(self) -> bool:
        f = self._frames()
        return len(f) == FRAMES and self._tenth_done(f[-1])

    def roll(self, pins: int) -> None:
        if self.is_over():
            raise GameOver()
        if not 0 <= pins <= PINS:
            raise InvalidRoll(pins)
        f = self._frames()
        if len(f) == FRAMES:
            if pins > self._standing_tenth(f[-1]):
                raise InvalidRoll(pins)
        elif f and len(f[-1]) == 1 and f[-1][0] != PINS and f[-1][0] + pins > PINS:
            raise InvalidRoll(pins)
        self._rolls.append(pins)

    # ---- scoring ----
    def frame_scores(self) -> list[int]:
        out, total, i, r = [], 0, 0, self._rolls
        for frame in range(FRAMES):
            if i >= len(r):
                break
            if r[i] == PINS:  # strike
                if i + 2 >= len(r):
                    break
                total += PINS + r[i + 1] + r[i + 2]
                i += 1
            else:
                if i + 1 >= len(r):
                    break
                if r[i] + r[i + 1] == PINS:  # spare
                    if i + 2 >= len(r):
                        break
                    total += PINS + r[i + 2]
                else:
                    total += r[i] + r[i + 1]
                i += 2
            out.append(total)
        return out

    def score(self) -> int:
        s = self.frame_scores()
        return s[-1] if s else 0
