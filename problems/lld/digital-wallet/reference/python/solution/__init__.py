from contract import WalletConfig, WalletService

from .service import Wallets


def create(config: WalletConfig) -> WalletService:
    return Wallets(config.max_transfer)
