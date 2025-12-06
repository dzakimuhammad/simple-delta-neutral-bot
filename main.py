import asyncio, yaml, time
from exchanges.hyperliquid import Hyperliquid
from exchanges.binance import BinanceFutures
from strategy.delta_neutral import DeltaNeutralStrategy
from utils.logger import log

async def main():
    cfg = yaml.safe_load(open("config.yaml"))

    exA = Hyperliquid(cfg["exchanges"]["hyperliquid"])
    exA.get_mid_price("BTC")

    # Closed all positions first

    # Evaluate mid price on both exchanges

    # Open long on lower price, short on higher price

    exA.market_order("BTC", "LONG", cfg["notional"])
    print("We wait for 5s before closing")
    time.sleep(5)
    
    exA.market_close("BTC")
if __name__ == "__main__":
    asyncio.run(main())
