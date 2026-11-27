from __future__ import annotations

import threading

from contract import (Broker, DuplicateSubscription, DuplicateTopic, InvalidArgument, InvalidOffset, Message,
                      UnknownGroup, UnknownTopic)


class Topic:
    """Append-only log. Appends are serialised; reads take a consistent snapshot length."""

    def __init__(self, name: str):
        self.name = name
        self._log: list[str] = []
        self._base = 0          # offset of _log[0]; earlier messages were dropped by retention
        self._retention = 0     # 0 = keep everything
        self._lock = threading.Lock()
        self.subscriptions: dict[str, Subscription] = {}

    def _trim(self) -> None:
        if self._retention and len(self._log) > self._retention:
            drop = len(self._log) - self._retention
            del self._log[:drop]
            self._base += drop

    def set_retention(self, max_messages: int) -> None:
        with self._lock:
            self._retention = max_messages
            self._trim()

    def append(self, payload: str) -> int:
        with self._lock:
            self._log.append(payload)
            self._trim()
            return self._base + len(self._log) - 1

    def start(self) -> int:
        with self._lock:
            return self._base

    def end(self) -> int:
        with self._lock:
            return self._base + len(self._log)

    def read(self, start: int, count: int) -> list[Message]:
        with self._lock:
            start = max(start, self._base)
            stop = min(start + count, self._base + len(self._log))
            return [Message(i, self._log[i - self._base]) for i in range(start, stop)]


class Subscription:
    """A consumer group's position in one topic. Read-and-advance is atomic."""

    def __init__(self, topic: Topic, position: int):
        self.topic = topic
        self.position = position
        self._lock = threading.Lock()

    def poll(self, max_count: int) -> list[Message]:
        with self._lock:
            batch = self.topic.read(self.position, max_count)
            if batch:
                self.position = batch[-1].offset + 1
            return batch

    def lag(self) -> int:
        with self._lock:
            return self.topic.end() - max(self.position, self.topic.start())

    def seek(self, offset: int) -> None:
        with self._lock:
            if not self.topic.start() <= offset <= self.topic.end():
                raise InvalidOffset(offset)
            self.position = offset


class InMemoryBroker(Broker):
    def __init__(self):
        self._topics: dict[str, Topic] = {}
        self._lock = threading.Lock()  # registry only

    def _topic(self, name: str) -> Topic:
        with self._lock:
            t = self._topics.get(name)
        if t is None:
            raise UnknownTopic(name)
        return t

    def _sub(self, topic: str, group: str) -> Subscription:
        t = self._topic(topic)
        with self._lock:
            s = t.subscriptions.get(group)
        if s is None:
            raise UnknownGroup(group)
        return s

    def create_topic(self, name: str) -> None:
        with self._lock:
            if name in self._topics:
                raise DuplicateTopic(name)
            self._topics[name] = Topic(name)

    def publish(self, topic: str, payload: str) -> int:
        return self._topic(topic).append(payload)

    def subscribe(self, topic: str, group: str, from_beginning: bool) -> None:
        t = self._topic(topic)
        with self._lock:
            if group in t.subscriptions:
                raise DuplicateSubscription(group)
            t.subscriptions[group] = Subscription(t, 0 if from_beginning else t.end())

    def poll(self, topic: str, group: str, max: int) -> list[Message]:
        if max < 1:
            raise InvalidArgument(max)
        return self._sub(topic, group).poll(max)

    def set_retention(self, topic: str, max_messages: int) -> None:
        if max_messages < 1:
            raise InvalidArgument(max_messages)
        self._topic(topic).set_retention(max_messages)

    def lag(self, topic: str, group: str) -> int:
        return self._sub(topic, group).lag()

    def seek(self, topic: str, group: str, offset: int) -> None:
        self._sub(topic, group).seek(offset)
