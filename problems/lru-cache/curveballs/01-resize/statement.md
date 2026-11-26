# Resize at runtime

Ops wants to change the cache size without a restart. `resize(capacity)`: if the cache now
holds more entries than the new capacity, evict least-recently-used entries until it fits.
Capacity below 1 raises `InvalidCapacity`.

*Interviewer's question:* how many places know the eviction rule?
