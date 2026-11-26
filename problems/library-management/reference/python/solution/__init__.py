from contract import Clock, Library, LibraryConfig

from .library import LendingLibrary
from .policy import PerDayFine


def create(config: LibraryConfig, clock: Clock) -> Library:
    return LendingLibrary(config.max_loans, config.loan_days, PerDayFine(config.fine_per_day), clock)
