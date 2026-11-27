from contract import Cache, CacheConfig

from .lru import LRUCache


def create(config: CacheConfig) -> Cache:
    return LRUCache(config.capacity)
