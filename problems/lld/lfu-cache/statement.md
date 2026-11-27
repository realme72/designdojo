# LFU Cache

Design a fixed-capacity cache that evicts the **least frequently used** key, breaking
ties by **least recently used**.

## Requirements

1. Capacity comes from config (always ≥ 1).
2. `get(key)` returns the value and counts as one use. Missing → `CacheMiss`.
3. `put(key, value)`: a new key starts with frequency 1; updating an existing key changes
   its value and counts as one use (no eviction). Inserting a new key into a full cache
   first evicts the key with the lowest frequency; among those, the least recently used.
4. `frequency(key)` returns how many times the key has been used (insert = 1). It does
   not count as a use. Missing → `CacheMiss`.
5. `size()` is the number of entries.
6. `get` and `put` must be O(1).
7. Operations must be thread-safe; size never exceeds capacity.

## Things an interviewer will push on

- How do you find the least-frequent, least-recent key in O(1)?
- What happens to an old hot key that's never used again ("frequency pollution")?
- Could LRU and LFU share code? Should they?
