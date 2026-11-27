from contract import LoadBalancer

from .balancer import Balancer


def create() -> LoadBalancer:
    return Balancer()
