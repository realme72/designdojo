from __future__ import annotations

from dataclasses import dataclass

from contract import DriverStatus, TripStatus, VehicleClass


@dataclass
class Driver:
    id: str
    vehicle: VehicleClass
    x: int
    y: int
    status: DriverStatus = DriverStatus.AVAILABLE


@dataclass
class TripRecord:
    id: str
    rider: str
    driver: str
    vehicle: VehicleClass
    pickup: tuple[int, int]
    dest: tuple[int, int]
    status: TripStatus = TripStatus.ASSIGNED
    fare: int = 0
    surge: int = 100  # percent in force when requested
