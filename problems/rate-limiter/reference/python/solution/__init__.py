from contract import Clock, RateLimiter

from .limiter import ClientRateLimiter


def create(clock: Clock) -> RateLimiter:
    return ClientRateLimiter(clock)
