import asyncio
from decimal import Decimal
from exchanges.base import Exchange
from models.asset import ExchangeAsset, TradingPair
from utils.logger import log
from models.order import Order, Side

'''
Delta Neutral Trading Strategy
1. Close existing positions on both exchanges
2. Compute PnL for closed positions
3. Fetch current prices from both exchanges
4. Open a long position on Exchange A and a short position on Exchange B with equal notional value. Long should be opened on the exchange with the lower price.
5. Track entry prices for both positions
'''
class DeltaNeutralStrategy:
    def __init__(self, exA: Exchange, exB: Exchange, cfg):
        self.A = exA    # Hyperliquid
        self.B = exB    # Binance
        self.notional = cfg["notional"]
        self.pair = TradingPair(cfg["base_asset"], cfg["quote_asset"])

        self.last_long_order: Order = None   # Order from long position
        self.last_short_order: Order = None  # Order from short position
        
        self.asset_A: ExchangeAsset = None  # ExchangeAsset for Hyperliquid
        self.asset_B: ExchangeAsset = None  # ExchangeAsset for Binance

    async def initialize(self):
        log(f"Initializing Delta Neutral Strategy on {self.A.name.value} and {self.B.name.value} for {self.pair.base_asset}")
        # Fetch asset info concurrently
        self.asset_A, self.asset_B = await asyncio.gather(
            self.A.get_asset_info(self.pair),
            self.B.get_asset_info(self.pair)
        )

        if self.asset_A.base_quantity_precision < self.asset_B.base_quantity_precision:
            log(f"Using {self.A.name.value} precision: {self.asset_A.base_quantity_precision} decimal places")
            self.asset_B.base_quantity_precision = self.asset_A.base_quantity_precision
        else:
            log(f"Using {self.B.name.value} precision: {self.asset_B.base_quantity_precision} decimal places")
            self.asset_A.base_quantity_precision = self.asset_B.base_quantity_precision
    
    async def cycle(self):
        # Close existing positions if any
        if self.last_long_order or self.last_short_order:
            log("Closing positions...")
            
            close_orders = []
            
            # Fetch prices concurrently
            price_A, price_B = await asyncio.gather(
                self.A.get_price(self.asset_A),
                self.B.get_price(self.asset_B)
            )
            
            # Determine which exchange has which position and prepare close tasks
            close_tasks = []
            
            # Check Hyperliquid
            if self.last_long_order and self.last_long_order.asset.exchange == self.asset_A.exchange:
                close_tasks.append(self.A.close_position(price_A))
            elif self.last_short_order and self.last_short_order.asset.exchange == self.asset_A.exchange:
                close_tasks.append(self.A.close_position(price_A))
            
            # Check Binance
            if self.last_long_order and self.last_long_order.asset.exchange == self.asset_B.exchange:
                close_tasks.append(self.B.close_position(price_B))
            elif self.last_short_order and self.last_short_order.asset.exchange == self.asset_B.exchange:
                close_tasks.append(self.B.close_position(price_B))
            
            # Close positions concurrently
            if close_tasks:
                close_orders = await asyncio.gather(*close_tasks)
            
            # Compute PnL for closed positions
            if len(close_orders) == 2:
                pnl = self.calculate_pnl(close_orders)
                log(f"Cycle Position PnL: ${pnl:.4f}")
            
            log("Positions closed.\n")

        # Fetch current prices from both exchanges concurrently
        price_A, price_B = await asyncio.gather(
            self.A.get_price(self.asset_A),
            self.B.get_price(self.asset_B)
        )
        
        log(f"{self.A.name.value} price: ${price_A:.4f}, {self.B.name.value} price: ${price_B:.4f}")
        # Determine which exchange has lower price for long position and open positions concurrently
        if price_A < price_B:
            log(f"Opening LONG on {self.A.name.value}, SHORT on {self.B.name.value}...")
            self.last_long_order, self.last_short_order = await asyncio.gather(
                self.A.open_long(self.asset_A, price_A, self.notional),
                self.B.open_short(self.asset_B, price_B, self.notional)
            )
        else:
            log(f"Opening LONG on {self.B.name.value}, SHORT on {self.A.name.value}...")
            self.last_long_order, self.last_short_order = await asyncio.gather(
                self.B.open_long(self.asset_B, price_B, self.notional),
                self.A.open_short(self.asset_A, price_A, self.notional)
            )
        
        # Calculate and log the price delta
        delta = float(self.last_long_order.price * self.last_long_order.size - self.last_short_order.price * self.last_short_order.size)
        pct = delta / float(self.last_long_order.price) * 100
        
        log(f"Entry Delta: ${delta:.4f} ({pct:.4f}%)")

    async def close_positions(self):
        """
        Close any open positions on both exchanges concurrently.
        This is called at the end of the cycle to ensure no positions are left open.
        """
        log(f"Closing positions...")
        close_tasks = []
        
        if self.last_long_order:
            if self.last_long_order.asset.exchange == self.A.name:
                close_tasks.append(self.A.close_position(self.last_long_order.price))
            else:
                close_tasks.append(self.B.close_position(self.last_long_order.price))
        
        if self.last_short_order:
            if self.last_short_order.asset.exchange == self.A.name:
                close_tasks.append(self.A.close_position(self.last_short_order.price))
            else:
                close_tasks.append(self.B.close_position(self.last_short_order.price))
        
        # Close all positions concurrently
        if close_tasks:
            close_orders = await asyncio.gather(*close_tasks)
        
        self.last_long_order = None
        self.last_short_order = None

        # Calculate PnL for closed positions
        pnl = self.calculate_pnl(close_orders)
        log(f"Cycle Position PnL: ${pnl:.4f}")
    
    def calculate_pnl(self, exit_orders: list[Order]) -> float:
        """
        Calculate PnL from entry and exit orders.
        s
        Args:
            exit_orders: List of exit Order objects (closing orders)
        
        Returns:
            Total PnL as float
        """
        if not self.last_long_order or not self.last_short_order:
            log("Warning: Missing long or short entry order")
            return 0.0
        
        # Find corresponding exit orders
        long_exit = None
        short_exit = None
        
        for order in exit_orders:
            # Closing a LONG position creates a SHORT order
            if order.side == Side.SHORT and order.asset.exchange == self.last_long_order.asset.exchange:
                long_exit = order
            # Closing a SHORT position creates a LONG order
            elif order.side == Side.LONG and order.asset.exchange == self.last_short_order.asset.exchange:
                short_exit = order
        
        if not long_exit or not short_exit:
            log("Warning: Missing long or short exit order")
            return 0.0
        
        # Calculate PnL for long position: (exit - entry) * size
        long_pnl = float((long_exit.price - self.last_long_order.price) * self.last_long_order.size)
        
        # Calculate PnL for short position: (entry - exit) * size
        short_pnl = float((self.last_short_order.price - short_exit.price) * self.last_short_order.size)
        
        total_pnl = long_pnl + short_pnl
        
        log(f"Long PnL: ${long_pnl:+.4f} (Entry: ${float(self.last_long_order.price):.4f}, Exit: ${float(long_exit.price):.4f})")
        log(f"Short PnL: ${short_pnl:+.4f} (Entry: ${float(self.last_short_order.price):.4f}, Exit: ${float(short_exit.price):.4f})")
        
        return total_pnl
