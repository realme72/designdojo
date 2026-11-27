from contract import Clock, Logging, LoggingConfig

from .logging_core import LogManager


def create(config: LoggingConfig, clock: Clock) -> Logging:
    return LogManager(config.root_level, clock)
