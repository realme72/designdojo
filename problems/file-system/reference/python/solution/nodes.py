from __future__ import annotations

from abc import ABC, abstractmethod


class Node(ABC):
    @abstractmethod
    def size(self) -> int: ...

    @abstractmethod
    def clone(self) -> "Node":
        """Deep copy (Prototype)."""

    @abstractmethod
    def files(self, prefix: str):
        """Yield (full_path, File) for every file at or under this node."""


class File(Node):
    def __init__(self, content: str = ""):
        self.content = content

    def size(self):
        return len(self.content)

    def clone(self):
        return File(self.content)

    def files(self, prefix):
        yield prefix, self


class Directory(Node):
    def __init__(self):
        self.children: dict[str, Node] = {}

    def size(self):
        return sum(c.size() for c in self.children.values())

    def clone(self):
        d = Directory()
        d.children = {name: child.clone() for name, child in self.children.items()}
        return d

    def files(self, prefix):
        for name, child in self.children.items():
            yield from child.files(f"{prefix.rstrip('/')}/{name}")
