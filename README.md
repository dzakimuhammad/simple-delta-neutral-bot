# Delta-Neutral Trading Bot

A Python-based automated trading bot that maintains delta-neutral positions across two perpetual futures exchanges (Hyperliquid and Binance) by opening and closing positions at regular intervals.

## 📋 Table of Contents
- [Overview](#overview)
- [Strategy Logic](#strategy-logic)
- [Features](#features)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Design Decisions](#design-decisions)
- [Limitations & Future Work](#limitations--future-work)
- [Safety Notes](#safety-notes)

## Overview

This bot implements a delta-neutral trading strategy by:
- Opening a long position on one exchange
- Opening a short position on another exchange with equal notional value
- Maintaining near-zero net delta exposure

## Strategy Logic

### What is Delta-Neutral Trading?

Delta-neutral trading is a strategy that aims to have zero or near-zero directional exposure to price movements. By simultaneously holding equal but opposite positions (long and short) on the same asset across different exchanges, the strategy seeks to profit from:
- **Price convergence**: When prices between exchanges converge
- **Funding rate arbitrage**: Differences in funding rates between perpetual futures contracts
- **Market inefficiencies**: Temporary price discrepancies between exchanges

### How This Bot Implements Delta-Neutral Strategy

#### 1. **Initialization Phase**
   - Connects to both Hyperliquid and Binance testnet exchanges
   - Fetches asset information (symbol format, quantity precision, etc.)
   - Synchronizes precision settings to ensure consistent position sizes
   - Uses the stricter precision requirement between the two exchanges

#### 2. **Trading Cycle Execution**

Each trading cycle follows this sequence:

**Step 1: Close Existing Positions (if any)**
   - If there are open positions from the previous cycle, close them simultaneously
   - Fetch current prices from both exchanges concurrently
   - Execute market orders to close both long and short positions
   - Calculate and log the PnL for the closed cycle

**Step 2: Calculate PnL**
   - **Long Position PnL**: `(Exit Price - Entry Price) × Position Size`
   - **Short Position PnL**: `(Entry Price - Exit Price) × Position Size`
   - **Total Cycle PnL**: Sum of both positions
   - Note: PnL calculation excludes trading fees for simplicity

**Step 3: Fetch Current Market Prices**
   - Query both exchanges simultaneously for the latest prices
   - Uses async operations for efficiency

**Step 4: Determine Position Allocation**
   - **Key Decision**: Open the long position on the exchange with the **lower price**
   - This maximizes the potential profit from price convergence
   - Example:
     - Hyperliquid BTC price: $89,207
     - Binance BTC price: $89,323
     - Action: **LONG on Hyperliquid**, **SHORT on Binance**

**Step 5: Open New Positions**
   - Calculate position size: `Position Size = Notional Value / Entry Price`
   - Open long and short positions concurrently using market orders
   - Both positions have equal notional value (e.g., $200)
   - Positions are matched in size but opposite in direction

**Step 6: Calculate Entry Delta**
   - Entry Delta = `(Long Price × Size) - (Short Price × Size)`
   - Measures the initial price difference between positions
   - A smaller delta indicates better entry execution

**Step 7: Wait for Next Cycle**
   - Sleep for the configured interval (e.g., 5 minutes)
   - Repeat the cycle until the maximum runtime is reached

#### 3. **Graceful Shutdown**
   - When the maximum runtime is reached, close all open positions
   - Calculate final PnL
   - Exit cleanly without leaving positions open

## ✨ Features

- **Multi-Exchange Support**: Integrates with Hyperliquid (testnet) and Binance Futures (testnet)
- **Delta-Neutral Strategy**: Automatically balances long and short positions
- **Configurable Intervals**: Set custom execution cycles
- **PnL Tracking**: Calculates profit/loss for each closed position
- **Async Operations**: Efficient concurrent API calls
- **Comprehensive Logging**: Timestamped logs with exchange, side, size, and price information

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Testnet accounts on:
  - [Hyperliquid Testnet](https://app.hyperliquid-testnet.xyz/)
  - [Binance Futures Testnet](https://testnet.binancefuture.com/)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/dzakimuhammad/simple-delta-neutral-bot.git
   cd simple-delta-neutral-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the bot**
   
   Copy the example configuration file:
   ```bash
   cp config.yaml.example config.yaml
   ```
   
   Or on Windows:
   ```cmd
   copy config.yaml.example config.yaml
   ```
   
   Edit `config.yaml` with your settings:
   
   ```yaml
   base_asset: BTC
   quote_asset: USDT
   notional: 200              # USD position size
   interval_minutes: 5        # Execution cycle interval
   max_runtime_minutes: 30    # Maximum Bot Run Time
   
   exchanges:
     hyperliquid:
       base_url: "https://api.hyperliquid-testnet.xyz"
       api_key: "YOUR_HYPERLIQUID_ACCOUNT_ADDRESS"
       api_secret: "YOUR_HYPERLIQUID_PRIVATE_KEY"
     binance:
       base_url: "https://testnet.binancefuture.com"
       api_key: "YOUR_BINANCE_API_KEY"
       api_secret: "YOUR_BINANCE_API_SECRET"
   ```

### Getting API Credentials

   **Hyperliquid Testnet:**
   - Create a wallet on [Hyperliquid testnet](https://app.hyperliquid-testnet.xyz/)
   - Use your wallet address as `api_key`
   - Export your private key as `api_secret`

   **Binance Futures Testnet:**
   - Register at [Binance Futures Testnet](https://testnet.binancefuture.com/)
   - Generate API key and secret from account settings
   - Enable futures trading permissions


## 💻 Usage

### Running the Bot

```bash
python main.py
```

The bot will:
1. Initialize connections to both exchanges
2. Fetch asset information and precision settings
3. Begin executing trading cycles at the configured interval
4. Run for the specified maximum time (default 30 minutes)
5. Close all positions and exit gracefully

### Expected Output

```
[16:12:19] Initializing Delta Neutral Strategy on Hyperliquid and Binance for BTC
[16:12:21] Using Binance precision: 3 decimal places
[16:12:21] Starting bot - BTC-PERP, $180 size, 5min interval
[16:12:22] Hyperliquid price: $89207.0000
[16:12:22] Binance price: $89323.3000
[16:12:22] Opening LONG on Hyperliquid, SHORT on Binance...
[16:12:25] Opening LONG 0.002 BTC on Hyperliquid @ $89214.0
[16:12:27] Opening SHORT 0.002 BTC on Binance @ $89323.3
[16:12:27] Entry Delta: $-0.2186 (-0.0002%)
[16:12:27] Waiting 5 minutes...

[16:17:27] Closing positions...
[16:17:33] Closed LONG BTC on Hyperliquid @ $89202.0
[16:17:36] Closed SHORT BTC on Binance @ $89325.7
[16:17:36] Long PnL: $-0.0240 (Entry: $89214.0000, Exit: $89202.0000)
[16:17:36] Short PnL: $-0.0048 (Entry: $89323.3000, Exit: $89325.7000)
[16:17:36] Cycle Position PnL: $-0.0288
[16:17:36] Positions closed.

[16:17:38] Hyperliquid price: $89209.5000
[16:17:38] Binance price: $89325.8000
[16:17:38] Opening LONG on Hyperliquid, SHORT on Binance...
[16:17:39] Opening LONG 0.002 BTC on Hyperliquid @ $89217.0
[16:17:42] Opening SHORT 0.002 BTC on Binance @ $89325.8
[16:17:42] Entry Delta: $-0.2176 (-0.0002%)
[16:17:42] Waiting 5 minutes...

[16:22:42] Closing positions...
[16:22:45] Closed LONG BTC on Hyperliquid @ $89069.0
[16:22:46] Closed SHORT BTC on Binance @ $89197.9
[16:22:46] Long PnL: $-0.2960 (Entry: $89217.0000, Exit: $89069.0000)
[16:22:46] Short PnL: $+0.2558 (Entry: $89325.8000, Exit: $89197.9000)
[16:22:46] Cycle Position PnL: $-0.0402
[16:22:46] Positions closed.

[16:22:46] Hyperliquid price: $89084.5000
[16:22:46] Binance price: $89197.9000
[16:22:46] Opening LONG on Hyperliquid, SHORT on Binance...
[16:22:48] Opening LONG 0.002 BTC on Hyperliquid @ $89104.0
[16:22:48] Opening SHORT 0.002 BTC on Binance @ $89197.9
[16:22:48] Entry Delta: $-0.1878 (-0.0002%)
[16:22:48] Waiting 5 minutes...

[16:27:48] Closing positions...
[16:27:50] Closed LONG BTC on Hyperliquid @ $88987.0
[16:27:52] Closed SHORT BTC on Binance @ $89124.5
[16:27:52] Long PnL: $-0.2340 (Entry: $89104.0000, Exit: $88987.0000)
[16:27:52] Short PnL: $+0.1468 (Entry: $89197.9000, Exit: $89124.5000)
[16:27:52] Cycle Position PnL: $-0.0872
[16:27:52] Positions closed.
...
```

## Project Structure

```
.
├── main.py                    # Entry point and main loop
├── config.yaml               # Configuration file (create from example)
├── config.yaml.example       # Example configuration
├── requirements.txt          # Python dependencies
├── exchanges/
│   ├── base.py              # Abstract Exchange base class
│   ├── binance.py           # Binance Futures implementation
│   └── hyperliquid.py       # Hyperliquid implementation
├── models/
│   ├── asset.py             # Trading pair and asset models
│   └── order.py             # Order data model
├── strategy/
│   └── delta_neutral.py     # Delta-neutral strategy logic
└── utils/
    └── logger.py            # Logging utility
```

## 🏗️ Design Decisions

### Exchange Integration Approach

#### Binance: REST API
- **Why REST API**: Binance Futures provides a well-documented REST API that doesn't require additional SDK dependencies
- **Implementation**: Direct HTTP requests using `aiohttp` for async operations
- **Benefits**:
  - Lightweight implementation with minimal dependencies
  - Full control over request signing and authentication
  - Easy to debug and customize
  - No version lock-in to specific SDK versions
- **Trade-offs**: Requires manual implementation of HMAC signature authentication and endpoint handling

#### Hyperliquid: Official Python SDK
- **Why SDK**: Hyperliquid's API requires Ethereum wallet integration and complex Web3 signing
- **Implementation**: Using `hyperliquid-python-sdk` (v0.21.0) with `eth-account` for wallet management
- **Benefits**:
  - Handles complex cryptographic operations (eth_account signing)
  - Abstracts away Web3-specific authentication logic
  - Maintained by the Hyperliquid team with updates for protocol changes
  - Simplifies order placement and position management
- **Trade-offs**: Additional dependency on SDK and its sub-dependencies

### Architecture Decisions

1. **Abstract Base Class Pattern**
   - `Exchange` base class defines common interface
   - Ensures consistency across different exchange implementations
   - Makes it easy to add new exchanges in the future

2. **Async/Await Pattern**
   - All API calls are asynchronous using `asyncio`
   - Enables concurrent operations (fetching prices, placing orders)
   - Improves performance and responsiveness

3. **Configuration-Driven**
   - YAML configuration for easy parameter adjustment
   - No code changes needed for different trading pairs or position sizes
   - Supports multiple environment setups (testnet/mainnet)

4. **Precision Handling**
   - Uses Python's `Decimal` for price and size calculations
   - Avoids floating-point arithmetic errors
   - Respects exchange-specific quantity precision requirements

5. **Simple PnL Calculation**
   - Calculates PnL without considering fees (as per requirements)
   - Shows individual position PnL and total cycle PnL

6. **Time-Limited Execution**
   - Bot runs for 30 minutes by default (configurable)
   - Ensures clean shutdown and position closure
   - Useful for testing and controlled execution

### Technology Stack

- **Python 3.8+**: Modern async/await support
- **aiohttp**: Async HTTP client for Binance API
- **PyYAML**: Configuration file parsing
- **eth-account**: Ethereum wallet management for Hyperliquid
- **hyperliquid-python-sdk**: Official Hyperliquid integration

## 🔮 Limitations & Future Work

### Current Limitations
- Uses market orders only (no limit orders)
- Supports one trading pair at a time
- Simplified PnL calculation without fees
- Configurable runtime (default 30 minutes)
- Testnet only

### Potential Enhancements
- Add limit order support for better execution prices
- Implement fee-adjusted PnL calculations
- Implement proper risk management (max position size, stop-loss)
- Add WebSocket connections for real-time price updates
- Add database for historical PnL tracking
- Support mainnet trading with proper safety checks
- Add multiple trading pair support

## ⚠️ Safety Notes

⚠️ **This bot is designed for testnet use only.** Before using with real funds:
- Implement comprehensive risk management
- Add position size limits and circuit breakers
- Include fee calculations in PnL
- Test thoroughly in testnet environments
- Add proper error handling and retry logic
- Implement monitoring and alerting systems

---

**Disclaimer**: This bot is for educational and testing purposes only. Use at your own risk.
