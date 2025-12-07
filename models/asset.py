from enum import Enum

class ExchangeName(Enum):
    HYPERLIQUID = "Hyperliquid"
    BINANCE = "Binance"

class TradingPair:
    base_asset: str
    quote_asset: str
    
    def __init__(self, base_asset: str, quote_asset: str):
        self.base_asset = base_asset
        self.quote_asset = quote_asset
    def __str__(self):
        return f"{self.base_asset}-{self.quote_asset}"
    def binance_symbol(self):
        return f"{self.base_asset}{self.quote_asset}"
    def hyperliquid_symbol(self):
        return f"{self.base_asset}"
    
class ExchangeAsset:
    pair: TradingPair
    exchange: ExchangeName
    exchange_symbol: str
    base_quantity_precision: int

    def __init__(self, pair: TradingPair, exchange: ExchangeName, exchange_symbol: str, base_quantity_precision: int):
        self.pair = pair
        self.exchange = exchange
        self.exchange_symbol = exchange_symbol
        self.base_quantity_precision = base_quantity_precision