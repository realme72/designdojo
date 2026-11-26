from contract import Clock, Notifier, NotifyConfig

from .service import NotificationService


def create(config: NotifyConfig, clock: Clock) -> Notifier:
    return NotificationService(config.max_per_hour, clock)
