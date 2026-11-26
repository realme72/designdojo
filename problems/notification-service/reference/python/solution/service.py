from __future__ import annotations

import re
import threading
from collections import defaultdict, deque

from contract import (Channel, Clock, Delivery, DuplicateTemplate, MissingVariable, Notifier, Priority, Status,
                      UnknownTemplate)

PLACEHOLDER = re.compile(r"\{([A-Za-z0-9_]+)\}")
HOUR = 3600


class Template:
    def __init__(self, body: str):
        self.body = body
        self.names = set(PLACEHOLDER.findall(body))

    def render(self, values: dict[str, str]) -> str:
        missing = self.names - set(values)
        if missing:
            raise MissingVariable(sorted(missing))
        return PLACEHOLDER.sub(lambda m: values[m.group(1)], self.body)  # single pass: values aren't re-rendered


class Sender:
    """One per channel; a real one would call an email/SMS/push provider."""

    def __init__(self, channel: Channel):
        self.channel = channel
        self.down = False
        self.outbox: defaultdict[str, list[str]] = defaultdict(list)

    def deliver(self, user: str, message: str) -> bool:
        if self.down:
            return False
        self.outbox[user].append(message)
        return True


class RateLimit:
    def __init__(self, max_per_hour: int, clock: Clock):
        self.max, self.clock = max_per_hour, clock
        self.sent: defaultdict[tuple[str, Channel], deque[int]] = defaultdict(deque)

    def allowed(self, key, priority: Priority) -> bool:
        now, log = self.clock.now(), self.sent[key]
        while log and log[0] <= now - HOUR:
            log.popleft()
        return priority is Priority.HIGH or len(log) < self.max

    def record(self, key) -> None:
        self.sent[key].append(self.clock.now())


class NotificationService(Notifier):
    def __init__(self, max_per_hour: int, clock: Clock):
        self._senders = {c: Sender(c) for c in Channel}  # registry: new channel = new Sender
        self._limits = RateLimit(max_per_hour, clock)
        self._prefs: dict[str, set[Channel]] = {}
        self._templates: dict[str, Template] = {}
        self._lock = threading.Lock()

    def set_preferences(self, user: str, channels: list[Channel]) -> None:
        with self._lock:
            self._prefs[user] = set(channels)

    def add_template(self, template_id: str, body: str) -> None:
        with self._lock:
            if template_id in self._templates:
                raise DuplicateTemplate(template_id)
            self._templates[template_id] = Template(body)

    def set_provider_down(self, channel: Channel, down: bool) -> None:
        with self._lock:
            self._senders[channel].down = down

    def send(self, user: str, template_id: str, vars: dict[str, str], priority: Priority) -> list[Delivery]:
        with self._lock:
            t = self._templates.get(template_id)
            if t is None:
                raise UnknownTemplate(template_id)
            message = t.render(vars)
            out = []
            for channel in Channel:  # enum order
                if channel not in self._prefs.get(user, ()):
                    continue
                key = (user, channel)
                if not self._limits.allowed(key, priority):
                    out.append(Delivery(channel, Status.RATE_LIMITED, message))
                elif self._senders[channel].deliver(user, message):
                    self._limits.record(key)
                    out.append(Delivery(channel, Status.SENT, message))
                else:
                    out.append(Delivery(channel, Status.FAILED, message))
            return out

    def outbox(self, user: str, channel: Channel) -> list[str]:
        with self._lock:
            return list(self._senders[channel].outbox.get(user, []))
