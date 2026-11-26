from contract import AuctionConfig, AuctionHouse, Clock

from .house import House


def create(config: AuctionConfig, clock: Clock) -> AuctionHouse:
    return House(config.extension_window, config.extension, clock)
