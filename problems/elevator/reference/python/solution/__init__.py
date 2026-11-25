from contract import BuildingConfig, ElevatorSystem

from .controller import Controller
from .dispatch import NearestOnTheWay


def create(config: BuildingConfig) -> ElevatorSystem:
    return Controller(config.floors, config.elevators, NearestOnTheWay())
