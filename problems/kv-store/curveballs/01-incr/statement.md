# Counters

Add `incr(key, by)`: treat the value as an integer, add `by`, store it back (as a string) and
return the new number. A missing key counts as 0. A value that isn't an integer raises
`InvalidValue` and changes nothing. Like every write, it is undone by `rollback`, and `count`
sees the new value.

*Interviewer's question:* did incr go through the same write path as set, or around it?
