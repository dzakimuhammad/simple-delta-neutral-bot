from abc import ABC, abstractmethod
from decimal import Decimal

from models.asset import ExchangeAsset, ExchangeName, TradingPair
from models.order import Order

class Exchange(ABC):
    # Attributes and methods that all exchange classes must implement
    name: ExchangeName
    base_url: str
    key: str
    secret: str
    last_order: Order

    @abstractmethod
    async def get_asset_info(self, pair: TradingPair) -> ExchangeAsset: ...

    @abstractmethod
    async def get_price(self, asset: ExchangeAsset) -> Decimal: ...

    @abstractmethod
    async def open_long(self, asset: ExchangeAsset, price: Decimal, notional: Decimal) -> Order: ...

    @abstractmethod
    async def open_short(self, asset: ExchangeAsset, price: Decimal, notional: Decimal) -> Order: ...

    @abstractmethod
    async def close_position(self, close_price: Decimal) -> Order: ...
