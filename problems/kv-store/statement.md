# Key-Value Store with Transactions

Design an in-memory key-value store that supports **nested transactions**.

## Requirements

1. `set(key, value)`, `get(key)` (missing → `KeyNotFound`), `delete(key)` (returns
   whether the key existed).
2. `count(value)` returns how many keys currently hold exactly that value.
   `keys(prefix)` returns the keys starting with `prefix`, sorted.
3. `begin()` opens a transaction; transactions nest.
4. `rollback()` discards every change made in the innermost open transaction.
   `commit()` merges the innermost transaction's changes into its parent (or into the
   store, if it is the outermost). With no open transaction both → `NoTransaction`.
5. Reads (`get`, `count`, `keys`) always see the current view, including uncommitted
   changes from all open transactions.
6. `count` must not scan every key.

## Things an interviewer will push on

- Undo log vs copy-on-write snapshot per transaction: memory and speed trade-offs?
- How do you keep `count(value)` O(1) across rollbacks?
- How would you add per-key TTL, or make it safe for several clients?
