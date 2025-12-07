from enum import Enum
from dataclasses import dataclass
from decimal import Decimal

from models.asset import ExchangeAsset

class Side(Enum):
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass
class Order:
    asset: ExchangeAsset
    side: Side
    price: Decimal
    size: Decimal