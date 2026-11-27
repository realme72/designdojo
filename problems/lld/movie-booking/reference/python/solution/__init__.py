from contract import BookingConfig, BookingSystem, Clock

from .system import Cinema


def create(config: BookingConfig, clock: Clock) -> BookingSystem:
    return Cinema(config.hold_seconds, clock)
