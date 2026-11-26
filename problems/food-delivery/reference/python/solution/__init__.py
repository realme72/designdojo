from contract import DeliveryConfig, FoodDelivery

from .notifications import CustomerInbox
from .platform import Platform


def create(config: DeliveryConfig) -> FoodDelivery:
    inbox = CustomerInbox()
    return Platform(config.delivery_fee, listeners=[inbox], inbox=inbox)
