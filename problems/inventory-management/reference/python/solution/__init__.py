from contract import Inventory

from .allocation import WarehouseOrder
from .inventory import StockService


def create() -> Inventory:
    return StockService(WarehouseOrder())
