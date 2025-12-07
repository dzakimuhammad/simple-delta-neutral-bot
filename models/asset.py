from enum import Enum
from dataclasses import dataclass

class Exchange(Enum):
    HYPERLIQUID = "HYPERLIQUID"
    BINANCE = "BINANCE"

@dataclass
class ExchangeAsset:
    pair: str
    exchange: Exchange
    exchange_symbol: str
    base_quantity_precision: int