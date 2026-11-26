from contract import Clinic, Clock

from .clinic import ClinicService


def create(clock: Clock) -> Clinic:
    return ClinicService(clock)
