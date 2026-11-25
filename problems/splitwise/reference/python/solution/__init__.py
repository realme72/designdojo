from contract import Splitwise

from .app import SplitwiseApp
from .splits import EqualSplit, ExactSplit, PercentSplit
from contract import SplitType


def create() -> Splitwise:
    return SplitwiseApp({SplitType.EQUAL: EqualSplit(), SplitType.EXACT: ExactSplit(),
                         SplitType.PERCENT: PercentSplit()})
