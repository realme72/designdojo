from contract import Cache, CacheConfig

from .lfu import LFUCache


def create(config: CacheConfig) -> Cache:
    return LFUCache(config.capacity)
