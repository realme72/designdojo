# Pinned entries

Some keys (feature flags) must never be evicted. `pin(key)` protects a cached key from
eviction; `unpin(key)` makes it evictable again (both raise `CacheMiss` for keys not in the
cache). Eviction picks the least-frequent, least-recently-used **unpinned** key. If every entry
is pinned and a new key is put into a full cache, raise `CacheFull` (updating an existing key
still works).

*Interviewer's question:* does your O(1) eviction survive this?
