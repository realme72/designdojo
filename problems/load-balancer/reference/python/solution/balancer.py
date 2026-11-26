from __future__ import annotations

import threading

from contract import (DuplicateServer, InvalidState, InvalidWeight, LoadBalancer, NoHealthyServer, Strategy,
                      UnknownServer)

from .strategies import RoundRobin, Server, make


class Balancer(LoadBalancer):
    def __init__(self):
        self._servers: dict[str, Server] = {}
        self._strategy = RoundRobin()
        self._sticky: dict[str, str] = {}  # client -> server
        self._lock = threading.Lock()

    def _server(self, sid: str) -> Server:
        s = self._servers.get(sid)
        if s is None:
            raise UnknownServer(sid)
        return s

    def add_server(self, server_id: str, weight: int) -> None:
        if weight < 1:
            raise InvalidWeight(weight)
        with self._lock:
            if server_id in self._servers:
                raise DuplicateServer(server_id)
            self._servers[server_id] = Server(server_id, weight)

    def remove_server(self, server_id: str) -> None:
        with self._lock:
            self._server(server_id)
            del self._servers[server_id]

    def set_healthy(self, server_id: str, healthy: bool) -> None:
        with self._lock:
            self._server(server_id).healthy = healthy

    def set_strategy(self, strategy: Strategy) -> None:
        with self._lock:
            self._strategy = make(strategy, list(self._servers.values()))

    def acquire(self) -> str:
        with self._lock:  # pick + count together
            healthy = sorted((s for s in self._servers.values() if s.healthy), key=lambda s: s.id)
            if not healthy:
                raise NoHealthyServer()
            s = self._strategy.pick(healthy)
            s.active += 1
            return s.id

    def acquire_for(self, client_id: str) -> str:
        with self._lock:
            s = self._servers.get(self._sticky.get(client_id, ""))
            if s is None or not s.healthy:
                healthy = sorted((s for s in self._servers.values() if s.healthy), key=lambda s: s.id)
                if not healthy:
                    raise NoHealthyServer()
                s = self._strategy.pick(healthy)
                self._sticky[client_id] = s.id
            s.active += 1
            return s.id

    def release(self, server_id: str) -> None:
        with self._lock:
            s = self._server(server_id)
            if s.active == 0:
                raise InvalidState(server_id)
            s.active -= 1

    def active(self, server_id: str) -> int:
        with self._lock:
            return self._server(server_id).active
