# LRU Cache

Design a fixed-capacity key-value cache that evicts the **least recently used** entry.

## Requirements

1. Capacity comes from config (always ≥ 1).
2. `get(key)` returns the value and marks the key most recently used. Missing → `CacheMiss`.
3. `put(key, value)` inserts or updates and marks the key most recently used. Inserting a
   new key into a full cache first evicts the least recently used key. Updating an existing
   key never evicts.
4. `delete(key)` removes a key; returns whether it existed.
5. `size()` is the number of entries; `keys()` lists keys from most to least recently used.
6. `get` and `put` must be O(1).
7. The cache is shared by many request threads: operations must be thread-safe and the
   size must never exceed capacity.

## Things an interviewer will push on

- Which data structures give O(1) for both get and put?
- How would you add per-entry TTL, or switch the policy to LFU?
- Is one global lock acceptable? What would you shard?
