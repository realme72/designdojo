from contract import Inventory

from .allocation import PriorityOrder
from .inventory import StockService


def create() -> Inventory:
    return StockService(PriorityOrder())
