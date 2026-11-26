# Time-range queries

Analytics wants "every record created since T" using the id index alone. Add
`min_id_at(timestamp)`: the smallest id any worker could generate at that epoch second, so
`id >= min_id_at(T)` selects everything from T on. A timestamp before the configured epoch
raises `InvalidTimestamp`.

*Interviewer's question:* how many places know the bit layout now?
