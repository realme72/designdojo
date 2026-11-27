from contract import BreakerConfig, CircuitBreakers, Clock

from .breaker import BreakerRegistry


def create(config: BreakerConfig, clock: Clock) -> CircuitBreakers:
    return BreakerRegistry(config, clock)
