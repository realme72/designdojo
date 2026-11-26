from __future__ import annotations

from contract import (AlreadyExists, DirectoryNotEmpty, FileSystem, InvalidPath, IsADirectory, NotADirectory,
                      NotFound)

from .nodes import Directory, File, Node


def parts(path: str) -> list[str]:
    if not path.startswith("/"):
        raise InvalidPath(path)
    p = path[1:]
    if p.endswith("/"):
        p = p[:-1]
    if not p:
        return []
    comps = p.split("/")
    if any(c in ("", ".", "..") for c in comps):
        raise InvalidPath(path)
    return comps


class MemoryFileSystem(FileSystem):
    def __init__(self):
        self.root = Directory()

    def _walk(self, comps: list[str]) -> Node:
        node: Node = self.root
        for c in comps:
            if not isinstance(node, Directory):
                raise NotADirectory(c)
            if c not in node.children:
                raise NotFound(c)
            node = node.children[c]
        return node

    def _parent(self, comps: list[str]) -> Directory:
        parent = self._walk(comps[:-1])
        if not isinstance(parent, Directory):
            raise NotADirectory("/".join(comps[:-1]))
        return parent

    def mkdir(self, path: str) -> None:
        node: Node = self.root
        for c in parts(path):
            if not isinstance(node, Directory):
                raise NotADirectory(c)
            node = node.children.setdefault(c, Directory())
        if not isinstance(node, Directory):
            raise NotADirectory(path)

    def write_file(self, path: str, content: str) -> None:
        comps = parts(path)
        if not comps:
            raise IsADirectory(path)
        parent = self._parent(comps)
        existing = parent.children.get(comps[-1])
        if isinstance(existing, Directory):
            raise IsADirectory(path)
        parent.children[comps[-1]] = File(content)

    def read_file(self, path: str) -> str:
        node = self._walk(parts(path))
        if not isinstance(node, File):
            raise IsADirectory(path)
        return node.content

    def ls(self, path: str) -> list[str]:
        comps = parts(path)
        node = self._walk(comps)
        if isinstance(node, File):
            return [comps[-1]]
        return sorted(node.children)

    def rm(self, path: str, recursive: bool) -> None:
        comps = parts(path)
        if not comps:
            raise InvalidPath(path)
        parent = self._parent(comps)
        node = parent.children.get(comps[-1])
        if node is None:
            raise NotFound(path)
        if isinstance(node, Directory) and node.children and not recursive:
            raise DirectoryNotEmpty(path)
        del parent.children[comps[-1]]

    def mv(self, src: str, dst: str) -> None:
        s, d = parts(src), parts(dst)
        if not s or d[:len(s)] == s:
            raise InvalidPath(f"{src} -> {dst}")
        src_parent = self._parent(s)
        node = src_parent.children.get(s[-1])
        if node is None:
            raise NotFound(src)
        if not d:
            raise AlreadyExists(dst)
        dst_parent = self._parent(d)
        if d[-1] in dst_parent.children:
            raise AlreadyExists(dst)
        del src_parent.children[s[-1]]
        dst_parent.children[d[-1]] = node

    def size(self, path: str) -> int:
        return self._walk(parts(path)).size()

    def find(self, path: str, suffix: str) -> list[str]:
        comps = parts(path)
        node = self._walk(comps)
        start = "/" + "/".join(comps)
        return sorted(p for p, _ in node.files(start) if p.rsplit("/", 1)[-1].endswith(suffix))
