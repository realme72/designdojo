from __future__ import annotations

import re
import threading
from dataclasses import dataclass

from contract import AliasTaken, Clock, Expired, InvalidAlias, InvalidUrl, Shortener, UnknownCode

from .codes import CodeGenerator

ALIAS = re.compile(r"^[A-Za-z0-9_-]{3,30}$")


@dataclass
class Link:
    url: str
    expires_at: int | None
    auto: bool
    clicks: int = 0

    def active(self, now: int) -> bool:
        return self.expires_at is None or now < self.expires_at


class ShortenerService(Shortener):
    def __init__(self, clock: Clock, codes: CodeGenerator):
        self._clock = clock
        self._codes = codes
        self._links: dict[str, Link] = {}
        self._auto_by_url: dict[str, str] = {}
        self._lock = threading.Lock()

    def shorten(self, long_url: str, alias: str, ttl_seconds: int) -> str:
        if not long_url.startswith(("http://", "https://")):
            raise InvalidUrl(long_url)
        if alias and not ALIAS.match(alias):
            raise InvalidAlias(alias)
        with self._lock:
            now = self._clock.now()
            expires = now + ttl_seconds if ttl_seconds > 0 else None
            if alias:
                if alias in self._links:
                    raise AliasTaken(alias)
                self._links[alias] = Link(long_url, expires, auto=False)
                return alias
            existing = self._auto_by_url.get(long_url)
            if existing in self._links and self._links[existing].active(now):
                return existing
            code = self._codes.next_code(lambda c: c in self._links)
            self._links[code] = Link(long_url, expires, auto=True)
            self._auto_by_url[long_url] = code
            return code

    def resolve(self, code: str) -> str:
        with self._lock:
            link = self._links.get(code)
            if link is None:
                raise UnknownCode(code)
            if not link.active(self._clock.now()):
                raise Expired(code)
            link.clicks += 1
            return link.url

    def clicks(self, code: str) -> int:
        with self._lock:
            link = self._links.get(code)
            if link is None:
                raise UnknownCode(code)
            return link.clicks

    def delete(self, code: str) -> None:
        with self._lock:
            if self._links.pop(code, None) is None:
                raise UnknownCode(code)
