from __future__ import annotations

import threading

from contract import (Broker, DuplicateSubscription, DuplicateTopic, InvalidArgument, InvalidOffset, Message,
                      UnknownGroup, UnknownTopic)


class Topic:
    """Append-only log. Appends are serialised; reads take a consistent snapshot length."""

    def __init__(self, name: str):
        self.name = name
        self._log: list[str] = []
        self._lock = threading.Lock()
        self.subscriptions: dict[str, Subscription] = {}

    def append(self, payload: str) -> int:
        with self._lock:
            self._log.append(payload)
            return len(self._log) - 1

    def end(self) -> int:
        with self._lock:
            return len(self._log)

    def read(self, start: int, count: int) -> list[Message]:
        with self._lock:
            return [Message(i, self._log[i]) for i in range(start, min(start + count, len(self._log)))]


class Subscription:
    """A consumer group's position in one topic. Read-and-advance is atomic."""

    def __init__(self, topic: Topic, position: int):
        self.topic = topic
        self.position = position
        self._lock = threading.Lock()

    def poll(self, max_count: int) -> list[Message]:
        with self._lock:
            batch = self.topic.read(self.position, max_count)
            self.position += len(batch)
            return batch

    def lag(self) -> int:
        with self._lock:
            return self.topic.end() - self.position

    def seek(self, offset: int) -> None:
        with self._lock:
            if not 0 <= offset <= self.topic.end():
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

    def lag(self, topic: str, group: str) -> int:
        return self._sub(topic, group).lag()

    def seek(self, topic: str, group: str, offset: int) -> None:
        self._sub(topic, group).seek(offset)
