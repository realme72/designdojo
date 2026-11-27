# JSON sink

The log pipeline team wants machine-readable logs. Add `add_json_sink(name, min_level)`
(repeated name → `DuplicateSink`). It behaves like any sink, but each line is a compact JSON
object with keys in this order:

`{"time":1700000000,"level":"INFO","logger":"app","message":"hi"}`

- No spaces. `time` is a number; the others are strings.
- Escape `"` as `\"`, `\` as `\\`, and newline as `\n`. Other characters are written as-is.

*Interviewer's question:* was this a new formatter, a new sink, or an edit to the existing one?
