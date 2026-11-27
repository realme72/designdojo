from contract import SocialNetwork

from .network import Network


def create() -> SocialNetwork:
    return Network()
