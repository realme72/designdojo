from contract import Atm, AtmConfig

from .bank import Bank
from .dispenser import Dispenser
from .machine import AtmMachine


def create(config: AtmConfig) -> Atm:
    return AtmMachine(Bank(config.accounts), Dispenser(dict(config.notes)))
