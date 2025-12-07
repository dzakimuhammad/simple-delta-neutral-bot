import aiohttp
import eth_account
from decimal import Decimal
from utils.logger import log
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange as HLExchange
from hyperliquid.utils import constants
from models.asset import ExchangeAsset, Exchange
from models.order import Order, Side

class Hyperliquid():
    def __init__(self, cfg):
        self.base = cfg["base_url"]
        self.key = cfg["api_key"]
        self.secret = cfg["api_secret"]

        account = eth_account.Account.from_key(self.secret)

        self.Info = Info(base_url=self.base, skip_ws=True)
        self.HLExchange = HLExchange(wallet=account, base_url=self.base, account_address=self.key)

    def get_asset_info(self, pair: str) -> ExchangeAsset:
        """Get asset info from Hyperliquid"""
        # For Hyperliquid, the pair is typically the asset name directly
        asset_name = pair.replace("-", "")
        
        try:
            hl_asset = self.Info.name_to_asset(asset_name)
            decimalSz = self.Info.asset_to_sz_decimals[hl_asset]
            
            return ExchangeAsset(
                pair=pair,
                exchange=Exchange.HYPERLIQUID,
                exchange_symbol=asset_name,
                base_quantity_precision=decimalSz
            )
        except Exception as e:
            log(f"Hyperliquid asset info not found for {pair}: {e}")
            raise Exception(f"Asset info not found for {pair}")

    def get_price(self, asset: ExchangeAsset) -> tuple[float, int]:
        all_mids = self.Info.all_mids()
        mid_price = all_mids[asset.exchange_symbol]
    
        hl_asset = self.Info.name_to_asset(asset.exchange_symbol)
        decimalSz = self.Info.asset_to_sz_decimals[hl_asset]

        return mid_price, decimalSz

    def market_order(self, asset: ExchangeAsset, side: Side, notional: float) -> Order:
        # Convert from notional to size in asset units
        mid_price, decimalSz = self.get_price(asset)
        size_in_asset = float(notional) / float(mid_price)
        size_in_asset = round(size_in_asset, decimalSz)

        is_buy = side == Side.LONG
        order_result = self.HLExchange.market_open(asset.exchange_symbol, is_buy, size_in_asset)
        
        if order_result["status"] == "ok":
            for status in order_result["response"]["data"]["statuses"]:
                try:
                    filled = status["filled"]
                    filled_price = Decimal(filled['avgPx'])
                    log(f"Opening {side.value} {size_in_asset} {asset.pair} on Hyperliquid @ {filled_price}")
                    
                    return Order(
                        asset=asset,
                        side=side,
                        price=filled_price,
                        size=Decimal(str(size_in_asset))
                    )
                except KeyError:
                    log(f'Error on opening {asset.pair} position on Hyperliquid: {status["error"]}')
                    raise Exception(f'Order failed: {status["error"]}')
        
        raise Exception(f"Order failed with status: {order_result.get('status', 'unknown')}")

    def open_long(self, asset: ExchangeAsset, notional: float) -> Order:
        """Open a long position"""
        return self.market_order(asset, Side.LONG, notional)

    def open_short(self, asset: ExchangeAsset, notional: float) -> Order:
        """Open a short position"""
        return self.market_order(asset, Side.SHORT, notional)

    def market_close(self, asset: ExchangeAsset, original_side: Side) -> Order:
        order_result = self.HLExchange.market_close(asset.exchange_symbol)
        
        if order_result["status"] == "ok":
            for status in order_result["response"]["data"]["statuses"]:
                try:
                    filled = status["filled"]
                    filled_price = Decimal(filled['avgPx'])
                    filled_size = Decimal(str(filled['totalSz']))
                    log(f"Closed {asset.pair} on Hyperliquid @ ${filled_price}")
                    
                    # Closing a long = short order, closing a short = long order
                    close_side = Side.SHORT if original_side == Side.LONG else Side.LONG
                    
                    return Order(
                        asset=asset,
                        side=close_side,
                        price=filled_price,
                        size=filled_size
                    )
                except KeyError:
                    log(f'Error on closing {asset.pair} position on Hyperliquid: {status["error"]}')
                    raise Exception(f'Close failed: {status["error"]}')
        
        raise Exception(f"Close failed with status: {order_result.get('status', 'unknown')}")
