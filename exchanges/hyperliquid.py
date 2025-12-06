import aiohttp
import eth_account
from utils.logger import log
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants

class Hyperliquid():
    def __init__(self, cfg):
        self.base = cfg["base_url"]
        self.key = cfg["api_key"]
        self.secret = cfg["api_secret"]

        account = eth_account.Account.from_key(self.secret)

        self.Info = Info(base_url=self.base, skip_ws=True)
        self.Exchange = Exchange(wallet=account, base_url=self.base, account_address=self.key)

    def get_mid_price(self, asset_name) -> tuple[float, int]:
        all_mids = self.Info.all_mids()
        mid_price = all_mids[asset_name]
    
        asset = self.Info.name_to_asset(asset_name)
        decimalSz = self.Info.asset_to_sz_decimals[asset]

        return mid_price, decimalSz

    def market_order(self, asset, side, size):
        # Convert from notional to size in asset units
        mid_price, decimalSz = self.get_mid_price(asset)
        size_in_asset = float(size) / float(mid_price)
        size_in_asset = round(size_in_asset, decimalSz)

        is_buy = side.lower() == "long"
        order_result = self.Exchange.market_open(asset, is_buy, size_in_asset)
        if order_result["status"] == "ok":
            for status in order_result["response"]["data"]["statuses"]:
                try:
                    filled = status["filled"]
                    log(f"Opening LONG {size_in_asset:.4f} {asset} on Hyperliquid @ {filled['avgPx']}")
                except KeyError:
                    log(f'Error on opening {asset} position on Hyperliquid: {status["error"]}')

    def market_close(self, asset, size=None):
        order_result = self.Exchange.market_close(asset)
        if order_result["status"] == "ok":
            for status in order_result["response"]["data"]["statuses"]:
                try:
                    filled = status["filled"]
                    log(f"Closed {asset} on Hyperliquid @ {filled['avgPx']}")
                except KeyError:
                    log(f'Error on closing {asset} position on Hyperliquid: {status["error"]}')
