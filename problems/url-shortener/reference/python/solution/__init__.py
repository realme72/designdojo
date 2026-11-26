from contract import Clock, Shortener

from .codes import Base62Sequence
from .service import ShortenerService


def create(clock: Clock) -> Shortener:
    return ShortenerService(clock, Base62Sequence(width=6))
