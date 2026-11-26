from __future__ import annotations

import threading

from contract import Algorithm, Clock, InvalidRule, RateLimiter, UnknownClient

from .algorithms import Limiter, make_limiter


class _Client:
    def __init__(self, limiter: Limiter):
        self.limiter = limiter
        self.lock = threading.Lock()


class ClientRateLimiter(RateLimiter):
    def __init__(self, clock: Clock):
        self._clock = clock
        self._clients: dict[str, _Client] = {}
        self._registry = threading.Lock()

    def configure(self, client_id: str, algorithm: Algorithm, limit: int, window_seconds: int) -> None:
        if limit < 1 or window_seconds < 1:
            raise InvalidRule(f"limit={limit} window={window_seconds}")
        client = _Client(make_limiter(algorithm, limit, window_seconds, self._clock.now()))
        with self._registry:
            self._clients[client_id] = client

    def allow(self, client_id: str) -> bool:
        with self._registry:
            client = self._clients.get(client_id)
        if client is None:
            raise UnknownClient(client_id)
        with client.lock:  # per-client: different clients never contend
            return client.limiter.allow(self._clock.now())
