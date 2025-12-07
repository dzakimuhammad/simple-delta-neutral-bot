import asyncio, yaml
from exchanges.hyperliquid import Hyperliquid
from exchanges.binance import BinanceFutures
from strategy.delta_neutral import DeltaNeutralStrategy
from utils.logger import log

async def main():
    try:
        cfg = yaml.safe_load(open("config.yaml"))
        max_runtime = cfg.get("max_runtime_minutes", 30)  # Default to 30 minutes if not specified

        exA = Hyperliquid(cfg["exchanges"]["hyperliquid"])
        exB = BinanceFutures(cfg["exchanges"]["binance"])

        strategy = DeltaNeutralStrategy(exA, exB, cfg)
        
        try:
            await strategy.initialize()
        except Exception as e:
            log(f"[ERROR] Strategy initialization failed: {e}")
            return

        interval = cfg["interval_minutes"] * 60

        log(f"Starting bot - {cfg['base_asset']}-PERP, ${cfg['notional']} size, {cfg['interval_minutes']}min interval")

        end_time = asyncio.get_event_loop().time() + (max_runtime * 60)
        while asyncio.get_event_loop().time() < end_time:
            try:
                await strategy.cycle()
                log(f"Waiting {cfg['interval_minutes']} minutes...\n")
                await asyncio.sleep(interval)
            except Exception as e:
                log(f"[ERROR] Cycle failed: {e}")
                await asyncio.sleep(interval)
        
        log(f"{max_runtime} minute limit reached. Stopping bot.")
        try:
            await strategy.close_positions()
        except Exception as e:
            log(f"[ERROR] Failed to close positions on shutdown: {e}")
            return
    
    except FileNotFoundError:
        log("[ERROR] config.yaml not found. Please create the config file.")
    except yaml.YAMLError as e:
        log(f"[ERROR] Invalid YAML in config.yaml: {e}")
    except KeyError as e:
        log(f"[ERROR] Missing required configuration key: {e}")
    except Exception as e:
        log(f"[ERROR] Unexpected error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main())
