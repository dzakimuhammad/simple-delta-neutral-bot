import eth_account
from decimal import Decimal
from exchanges.base import Exchange
from utils.logger import log
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange as HLExchange
from models.asset import ExchangeAsset, ExchangeName, TradingPair
from models.order import Order, Side

class Hyperliquid(Exchange):
    def __init__(self, cfg):
        self.name = ExchangeName.HYPERLIQUID
        self.base_url = cfg["base_url"]
        self.key = cfg["api_key"]
        self.secret = cfg["api_secret"]
        self.last_order: Order = None

        account = eth_account.Account.from_key(self.secret)

        self.Info = Info(base_url=self.base_url, skip_ws=True)
        self.HLExchange = HLExchange(wallet=account, base_url=self.base_url, account_address=self.key)

    async def get_asset_info(self, pair: TradingPair) -> ExchangeAsset:
        """Get asset info from Hyperliquid"""
        # For Hyperliquid, the pair is typically the asset name directly
        # e.g., "BTC-USDT" -> "BTC"
        asset_name = pair.hyperliquid_symbol()
        
        try:
            hl_asset = self.Info.name_to_asset(asset_name)
            decimalSz = self.Info.asset_to_sz_decimals[hl_asset]
            
            return ExchangeAsset(
                pair=pair,
                exchange=self.name,
                exchange_symbol=asset_name,
                base_quantity_precision=decimalSz
            )
        except Exception as e:
            log(f"Hyperliquid asset info not found for {asset_name}: {e}")
            raise

    async def get_price(self, asset: ExchangeAsset) -> float:
        all_mids = self.Info.all_mids()
        mid_price = all_mids[asset.exchange_symbol]
        return float(mid_price)

    async def open_position(self, asset: ExchangeAsset, side: Side, price: float, notional: float) -> Order:
        # Convert from notional to size in asset units
        qty = round(notional / price, asset.base_quantity_precision)

        is_buy = side == Side.LONG

        try:
            order_result = self.HLExchange.market_open(asset.exchange_symbol, is_buy, qty)
        
            if order_result["status"] == "ok":
                for status in order_result["response"]["data"]["statuses"]:
                    try:
                        filled = status["filled"]
                        filled_price = Decimal(filled['avgPx'])
                        log(f"Opening {side.value} {qty} {asset.pair.base_asset} on Hyperliquid @ ${filled_price}")
                        
                        order = Order(
                            asset=asset,
                            side=side,
                            price=filled_price,
                            size=Decimal(str(qty))
                        )
                        self.last_order = order
                        return order
                    except KeyError:
                        log(f'Error on opening {asset.pair.base_asset} position on Hyperliquid: {status["error"]}')
                        raise Exception(f'Order failed: {status["error"]}')
        except Exception as e:
            log(f"Exception during market order on Hyperliquid: {e}")
            raise

    async def open_long(self, asset: ExchangeAsset, price: float, notional: float) -> Order:
        """Open a long position"""
        return await self.open_position(asset, Side.LONG, price, notional)

    async def open_short(self, asset: ExchangeAsset, price: float,  notional: float) -> Order:
        """Open a short position"""
        return await self.open_position(asset, Side.SHORT, price, notional)
    async def close_position(self, close_price: float) -> Order:
        if not self.last_order:
            raise Exception("No position to close")
            
        order_result = self.HLExchange.market_close(self.last_order.asset.exchange_symbol)
        
        if order_result["status"] == "ok":
            for status in order_result["response"]["data"]["statuses"]:
                try:
                    filled = status["filled"]
                    filled_price = Decimal(filled['avgPx'])
                    filled_size = Decimal(str(filled['totalSz']))
                    log(f"Closed {self.last_order.side.value} {self.last_order.asset.pair.base_asset} on Hyperliquid @ ${filled_price}")
                    
                    # Closing a long = short order, closing a short = long order
                    close_side = Side.SHORT if self.last_order.side == Side.LONG else Side.LONG
                    
                    close_order = Order(
                        asset=self.last_order.asset,
                        side=close_side,
                        price=filled_price,
                        size=filled_size
                    )
                    return close_order
                except KeyError:
                    log(f'Error on closing {self.last_order.asset.pair.base_asset} position on Hyperliquid: {status["error"]}')
                    raise Exception(f'Close failed: {status["error"]}')
        
        raise Exception(f"Close failed with status: {order_result.get('status', 'unknown')}")
