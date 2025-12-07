import aiohttp, time, hmac, hashlib
from decimal import Decimal
from exchanges.base import Exchange
from utils.logger import log
from models.asset import ExchangeAsset, ExchangeName, TradingPair
from models.order import Order, Side

class BinanceFutures(Exchange):
    def __init__(self, cfg):
        self.name = ExchangeName.BINANCE
        self.base_url = cfg["base_url"]
        self.key = cfg["api_key"]
        self.secret = cfg["api_secret"]
        self.last_order = None

    def _sign(self, params):
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        sig = hmac.new(
            self.secret.encode(), query.encode(), hashlib.sha256
        ).hexdigest()
        return query + "&signature=" + sig

    async def get_asset_info(self, pair: TradingPair) -> ExchangeAsset:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/fapi/v1/exchangeInfo") as r:
                data = await r.json()
                if "symbols" not in data or len(data["symbols"]) == 0:
                    raise Exception(f"Error getting asset info: {data}")
                for sym in data["symbols"]:
                    if sym["symbol"] == pair.binance_symbol():
                        return ExchangeAsset(
                            pair=pair,
                            exchange=self.name,
                            exchange_symbol=sym["symbol"],
                            base_quantity_precision=sym["quantityPrecision"]
                        )
                log(f"Binance asset info not found for {pair}")
                raise Exception(f"Asset info not found for {pair}")
    
    async def get_price(self, asset: ExchangeAsset) -> float:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/fapi/v2/ticker/price?symbol={asset.exchange_symbol}") as r:
                data = await r.json()
                if "price" not in data:
                    raise Exception(f"Error getting price: {data}")
                return float(data["price"])

    async def open_position(self, asset: ExchangeAsset, side: Side, price: float, notional: float) -> Order:
        qty = round(notional / price, asset.base_quantity_precision)

        params = {
            "symbol": asset.exchange_symbol,
            "side": "BUY" if side == Side.LONG else "SELL",
            "type": "MARKET",
            "quantity": qty,
            "timestamp": int(time.time() * 1000),
        }

        url = f"{self.base_url}/fapi/v1/order?{self._sign(params)}"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers={"X-MBX-APIKEY": self.key}) as r:
                data = await r.json()
                if "code" in data and data["code"] != 200:
                    log(f"[ERROR] Binance order error: {data}")
                    raise Exception(f"Order failed: {data['msg'] if 'msg' in data else 'Unknown error'}")

        order = Order(
            asset=asset,
            side=side,
            price=Decimal(str(price)),
            size=Decimal(str(qty))
        )
        self.last_order = order
        log(f"Opening {side.value} {qty} {asset.pair.base_asset} on Binance @ ${price}")
        return order

    async def open_long(self, asset: ExchangeAsset, price: float, notional: float) -> Order:
        return await self.open_position(asset, Side.LONG, price, notional)

    async def open_short(self, asset: ExchangeAsset, price: float, notional: float) -> Order:
        return await self.open_position(asset, Side.SHORT, price, notional)

    async def close_position(self, close_price: float) -> Order:
        """Close a position by placing opposite side order"""
        if not self.last_order:
            raise Exception("No position to close")
            
        close_side = "BUY" if self.last_order.side == Side.SHORT else "SELL"

        params = {
            "symbol": self.last_order.asset.exchange_symbol,
            "side": close_side,
            "type": "MARKET",
            "quantity": float(self.last_order.size),
            "timestamp": int(time.time() * 1000),
        }

        url = f"{self.base_url}/fapi/v1/order?{self._sign(params)}"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers={"X-MBX-APIKEY": self.key}) as r:
                data = await r.json()
                if "code" in data and data["code"] != 200:
                    log(f"[Error] Binance close error: {data}")
                    raise Exception(f"Close failed: {data['msg'] if 'msg' in data else 'Unknown error'}")

        close_order = Order(
            asset=self.last_order.asset,
            side=Side.SHORT if self.last_order.side == Side.LONG else Side.LONG,
            price=Decimal(str(close_price)),
            size=self.last_order.size
        )
        log(f"Closed {self.last_order.side.value} {self.last_order.asset.pair.base_asset} on Binance @ ${close_price}")
        return close_order
