from contract import InningsConfig, Scoreboard

from .innings import Innings


def create(config: InningsConfig) -> Scoreboard:
    return Innings(config.overs, list(config.batters))
