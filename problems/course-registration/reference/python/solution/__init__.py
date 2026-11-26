from contract import Registrar, RegistrationConfig

from .registrar import University


def create(config: RegistrationConfig) -> Registrar:
    return University(config.max_courses)
