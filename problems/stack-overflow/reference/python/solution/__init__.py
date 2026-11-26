from contract import QaSite, SiteConfig

from .site import Site, StandardReputation


def create(config: SiteConfig) -> QaSite:
    return Site(config.close_threshold, StandardReputation())
