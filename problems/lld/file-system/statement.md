# In-memory File System

Design a Unix-like file system that lives in memory.

## Requirements

1. Paths are absolute: `/`, `/a`, `/a/b`. A trailing `/` is ignored. Not starting with `/`,
   empty components (`//`), `.` or `..` → `InvalidPath`.
2. `mkdir(path)` creates the directory and any missing parents (like `mkdir -p`; existing
   directories are fine). A path component that is a file → `NotADirectory`.
3. `write_file(path, content)` creates or overwrites a file. Missing parent → `NotFound`;
   a parent that is a file → `NotADirectory`; path is a directory → `IsADirectory`.
4. `read_file(path)` → content (`NotFound`, `IsADirectory`).
5. `ls(path)`: a directory → its entry names sorted; a file → `[name]`. Missing → `NotFound`.
6. `rm(path, recursive)`: removing a non-empty directory without `recursive` →
   `DirectoryNotEmpty`; removing `/` → `InvalidPath`; missing → `NotFound`.
7. `mv(src, dst)` moves a file or directory to the new path. `dst` exists → `AlreadyExists`;
   `dst`'s parent missing → `NotFound`; moving a directory into itself or its own subtree →
   `InvalidPath`; moving `/` → `InvalidPath`.
8. `size(path)` → total content length of the file, or of all files under a directory.
9. `find(path, suffix)` → full paths of all **files** under `path` whose name ends with
   `suffix`, sorted.

## Things an interviewer will push on

- File and Directory: one Node hierarchy (Composite) or separate classes?
- How would you add permissions, symlinks or hard links?
- Path resolution: where does it live, and how is it tested?
