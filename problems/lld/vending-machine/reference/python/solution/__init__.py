from contract import MachineConfig, VendingMachine

from .machine import Machine


def create(config: MachineConfig) -> VendingMachine:
    return Machine(dict(config.coins))
