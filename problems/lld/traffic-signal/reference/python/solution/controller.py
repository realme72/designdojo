from __future__ import annotations

from dataclasses import dataclass

from contract import Clock, Color, Direction, InvalidDuration, Mode, Phase, SignalConfig, TrafficSignal

G, Y, R = Color.GREEN, Color.YELLOW, Color.RED


@dataclass(frozen=True)
class PhaseSpec:
    next: Phase
    timing: str  # which config duration
    ns: Color
    ew: Color


TABLE = {
    Phase.NS_GREEN: PhaseSpec(Phase.NS_YELLOW, "green", G, R),
    Phase.NS_YELLOW: PhaseSpec(Phase.ALL_RED_TO_EW, "yellow", Y, R),
    Phase.ALL_RED_TO_EW: PhaseSpec(Phase.EW_GREEN, "all_red", R, R),
    Phase.EW_GREEN: PhaseSpec(Phase.EW_YELLOW, "green", R, G),
    Phase.EW_YELLOW: PhaseSpec(Phase.ALL_RED_TO_NS, "yellow", R, Y),
    Phase.ALL_RED_TO_NS: PhaseSpec(Phase.NS_GREEN, "all_red", R, R),
}
GREEN_OF = {Direction.NS: Phase.NS_GREEN, Direction.EW: Phase.EW_GREEN}


class Controller(TrafficSignal):
    def __init__(self, config: SignalConfig, clock: Clock):
        self._cfg, self._clock = config, clock
        self._mode = Mode.NORMAL
        self._greens: dict[Phase, int] = {}
        self._restart(Phase.NS_GREEN)

    def _restart(self, phase: Phase) -> None:
        self._phase, self._started = phase, self._clock.now()

    def _duration(self, phase: Phase) -> int:
        if phase in self._greens:
            return self._greens[phase]
        return getattr(self._cfg, TABLE[phase].timing)

    def set_green(self, direction: Direction, seconds: int) -> None:
        if seconds < 1:
            raise InvalidDuration(seconds)
        if self._mode is Mode.NORMAL:
            self._advance()  # settle the phase under the old timings first
        self._greens[GREEN_OF[direction]] = seconds

    def _advance(self) -> None:
        now = self._clock.now()
        cycle = sum(self._duration(p) for p in TABLE)
        if now - self._started >= cycle:  # skip whole cycles in O(1)
            self._started += (now - self._started) // cycle * cycle
        while now >= self._started + self._duration(self._phase):
            self._started += self._duration(self._phase)
            self._phase = TABLE[self._phase].next

    def phase(self) -> Phase:
        if self._mode is Mode.FLASHING:
            return Phase.FLASHING
        self._advance()
        return self._phase

    def remaining(self) -> int:
        if self._mode is Mode.FLASHING:
            return 0
        self._advance()
        return self._started + self._duration(self._phase) - self._clock.now()

    def light(self, direction: Direction) -> Color:
        if self._mode is Mode.FLASHING:
            return Y
        self._advance()
        spec = TABLE[self._phase]
        return spec.ns if direction is Direction.NS else spec.ew

    def emergency(self, direction: Direction) -> None:
        if self._mode is Mode.FLASHING:
            return
        self._advance()
        if self._phase is GREEN_OF[direction]:
            self._restart(self._phase)
        elif self._phase in GREEN_OF.values():
            self._restart(TABLE[self._phase].next)

    def set_mode(self, mode: Mode) -> None:
        if mode is Mode.NORMAL and self._mode is Mode.FLASHING:
            self._restart(Phase.NS_GREEN)
        self._mode = mode
