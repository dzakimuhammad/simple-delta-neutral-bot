from enum import Enum
from decimal import Decimal

from models.asset import ExchangeAsset

class Side(Enum):
    LONG = "LONG"
    SHORT = "SHORT"

class Order:
    asset: ExchangeAsset
    side: Side
    price: Decimal
    size: Decimal

    def __init__(self, asset: ExchangeAsset, side: Side, price: Decimal, size: Decimal):
        self.asset = asset
        self.side = side
        self.price = price
        self.size = size