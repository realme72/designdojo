from __future__ import annotations

import threading

from contract import BreakerConfig, BreakerState, CircuitBreakers, Clock


class _State:
    name: BreakerState

    def enter(self, b: "Breaker") -> None: ...
    def allow(self, b: "Breaker") -> bool: raise NotImplementedError
    def success(self, b: "Breaker") -> None: ...
    def failure(self, b: "Breaker") -> None: ...


class _Closed(_State):
    name = BreakerState.CLOSED

    def enter(self, b):
        b.failures = 0

    def allow(self, b):
        return True

    def success(self, b):
        b.failures = 0

    def failure(self, b):
        b.failures += 1
        if b.failures >= b.cfg.failure_threshold:
            b.go(OPEN)


class _Open(_State):
    name = BreakerState.OPEN

    def enter(self, b):
        b.opened_at = b.clock.now()

    def allow(self, b):
        return False


class _HalfOpen(_State):
    name = BreakerState.HALF_OPEN

    def enter(self, b):
        b.permits = b.cfg.trial_requests
        b.successes = 0

    def allow(self, b):
        if b.permits > 0:
            b.permits -= 1
            return True
        return False

    def success(self, b):
        b.successes += 1
        if b.successes >= b.cfg.trial_requests:
            b.go(CLOSED)

    def failure(self, b):
        b.go(OPEN)


CLOSED, OPEN, HALF_OPEN = _Closed(), _Open(), _HalfOpen()


class Breaker:
    def __init__(self, cfg: BreakerConfig, clock: Clock):
        self.cfg, self.clock = cfg, clock
        self.lock = threading.Lock()
        self.failures = self.permits = self.successes = 0
        self.opened_at = 0
        self.state: _State = CLOSED

    def go(self, state: _State) -> None:
        self.state = state
        state.enter(self)

    def current(self) -> _State:
        """Lazy OPEN -> HALF_OPEN once the open period has elapsed."""
        if self.state is OPEN and self.clock.now() >= self.opened_at + self.cfg.open_seconds:
            self.go(HALF_OPEN)
        return self.state


class BreakerRegistry(CircuitBreakers):
    def __init__(self, config: BreakerConfig, clock: Clock):
        self._cfg, self._clock = config, clock
        self._breakers: dict[str, Breaker] = {}
        self._lock = threading.Lock()

    def _get(self, service: str) -> Breaker:
        with self._lock:
            b = self._breakers.get(service)
            if b is None:
                b = self._breakers[service] = Breaker(self._cfg, self._clock)
            return b

    def allow_request(self, service: str) -> bool:
        b = self._get(service)
        with b.lock:
            return b.current().allow(b)

    def record_success(self, service: str) -> None:
        b = self._get(service)
        with b.lock:
            b.current().success(b)

    def record_failure(self, service: str) -> None:
        b = self._get(service)
        with b.lock:
            b.current().failure(b)

    def state(self, service: str) -> BreakerState:
        b = self._get(service)
        with b.lock:
            return b.current().name
