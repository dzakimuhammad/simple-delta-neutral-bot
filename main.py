import asyncio, yaml
from exchanges.hyperliquid import Hyperliquid
from exchanges.binance import BinanceFutures
from strategy.delta_neutral import DeltaNeutralStrategy
from utils.logger import log

async def main():
    cfg = yaml.safe_load(open("config.yaml"))
    max_runtime = cfg.get("max_runtime_minutes", 30)  # Default to 30 minutes if not specified

    exA = Hyperliquid(cfg["exchanges"]["hyperliquid"])
    exB = BinanceFutures(cfg["exchanges"]["binance"])

    strategy = DeltaNeutralStrategy(exA, exB, cfg)
    await strategy.initialize()

    interval = cfg["interval_minutes"] * 60

    log(f"Starting bot - {cfg['base_asset']}-PERP, ${cfg['notional']} size, {cfg['interval_minutes']}min interval")

    end_time = asyncio.get_event_loop().time() + (max_runtime * 60)
    while asyncio.get_event_loop().time() < end_time:
        await strategy.cycle()
        log(f"Waiting {cfg['interval_minutes']} minutes...\n")
        await asyncio.sleep(interval)
    log(f"{max_runtime} minute limit reached. Stopping bot.")
    await strategy.close_positions()

if __name__ == "__main__":
    asyncio.run(main())
