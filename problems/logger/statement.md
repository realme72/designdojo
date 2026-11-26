# Logging Framework

Design a small logging library (think a minimal log4j/logging module).

## Requirements

1. Levels, low to high: `DEBUG < INFO < WARN < ERROR < FATAL`.
2. Loggers are named hierarchically with dots (`app`, `app.db`, `app.db.pool`). A logger's
   **effective level** is the level set on the most specific ancestor-or-self via
   `set_level(logger, level)`; if none, the root level from config. (`app.db` inherits from
   `app`; `apple` is *not* a child of `app`.)
3. `log(logger, level, message)`: if `level` ≥ the logger's effective level, the record
   goes to every sink whose `min_level` ≤ `level`. Returns how many sinks wrote it.
4. `add_sink(name, min_level, format)`: a destination with a format template using
   `{time}` (clock epoch seconds), `{level}`, `{logger}`, `{message}`. Any other
   `{placeholder}` → `InvalidFormat`. Repeated name → `DuplicateSink`.
5. `remove_sink(name)`; `output(name)` returns the lines that sink has written, in order.
   Unknown sink → `UnknownSink`.
6. Many threads log at once: no line may be lost or interleaved.

## Things an interviewer will push on

- How do you add a new sink type (file, network) without touching the logger?
- Where does filtering happen: logger, sink, or a chain of handlers?
- How would you make logging asynchronous without losing ordering?
