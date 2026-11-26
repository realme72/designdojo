# Copy

Add `copy(src, dst)`: a deep copy of a file or a whole directory tree. Afterwards the copy is
independent: writing to it never changes the original. Same errors as `mv`: missing source →
`NotFound`, existing destination → `AlreadyExists`, missing destination parent → `NotFound`,
copying a directory into itself → `InvalidPath`.

*Interviewer's question:* who knows how to copy a node: the file system or the node?
