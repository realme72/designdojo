from contract import FileSystem

from .fs import MemoryFileSystem


def create() -> FileSystem:
    return MemoryFileSystem()
