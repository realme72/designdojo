from __future__ import annotations

import threading
from dataclasses import dataclass

from contract import ClockMovedBackwards, Clock, IdGenerator, IdParts, SequenceExhausted

WORKER_BITS = 10


@dataclass(frozen=True)
class Layout:
    sequence_bits: int

    @property
    def max_sequence(self) -> int:
        return (1 << self.sequence_bits) - 1

    def pack(self, ts: int, worker: int, seq: int) -> int:
        return (ts << (WORKER_BITS + self.sequence_bits)) | (worker << self.sequence_bits) | seq

    def unpack(self, value: int) -> tuple[int, int, int]:
        seq = value & self.max_sequence
        worker = (value >> self.sequence_bits) & ((1 << WORKER_BITS) - 1)
        ts = value >> (WORKER_BITS + self.sequence_bits)
        return ts, worker, seq


class Snowflake(IdGenerator):
    def __init__(self, layout: Layout, epoch: int, worker: int, clock: Clock):
        self._layout, self._epoch, self._worker, self._clock = layout, epoch, worker, clock
        self._last = -1
        self._seq = -1
        self._lock = threading.Lock()

    def next_id(self) -> int:
        with self._lock:
            ts = self._clock.now() - self._epoch
            if ts < self._last:
                raise ClockMovedBackwards(f"{ts} < {self._last}")
            if ts == self._last:
                if self._seq >= self._layout.max_sequence:
                    raise SequenceExhausted(ts)
                self._seq += 1
            else:
                self._last, self._seq = ts, 0
            return self._layout.pack(ts, self._worker, self._seq)

    def parse(self, id: int) -> IdParts:
        ts, worker, seq = self._layout.unpack(id)
        return IdParts(ts + self._epoch, worker, seq)
