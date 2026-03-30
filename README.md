# stocks.py

A simple CLI for getting stock market data from Yahoo Finance.

## Features

- **Single-file executable** - Uses `uv run --script` with inline dependencies (PEP 723)
- **Stock quotes** - Price, valuation metrics, volume, sector, and more
- **Moving averages** - SMA (20/50/200-day) and EMA (9/21-day) with position analysis
- **Trading signals** - Golden Cross, Death Cross, trend alignment, EMA crossovers
- **Ticker search** - Find symbols by company name
- **Historical data** - OHLCV data with configurable periods and intervals
- **PNG charts** - Candlestick and line charts with transparent/white/black backgrounds

## Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager

## Installation

### Install for uv

```bash
# Clone the repo
git clone https://github.com/vicgarcia/stocks.py

# Run directly (dependencies auto-installed)
uv run --script scripts/stocks.py --help

# Install in PATH
cp scripts/stocks.py ~/.local/bin/stocks.py
chmod +x ~/.local/bin/stocks.py
stocks.py --help
```

### Install for Claude Desktop

Download `stocks-v*.zip` from [Releases](https://github.com/vicgarcia/stocks.py/releases).
Install in Claude Desktop as a skill.

## Commands

| Command | Description |
|---------|-------------|
| `quote` | Get stock quote with moving averages |
| `search` | Search for ticker symbols by company name |
| `history` | Get historical OHLCV data |
| `chart` | Generate PNG chart |

## Usage

### Stock Quote

```bash
# Basic quote
stocks.py quote AAPL

# With trading signals
stocks.py quote TSLA --signals
stocks.py quote NVDA -s
```

Output includes:
- Current price and market cap
- P/E ratios (trailing and forward)
- Dividend yield
- 52-week high/low
- Volume metrics
- Sector and industry
- Moving averages with position (above/below)
- Trading signals (with `--signals` flag)

### Search Tickers

```bash
# Search by company name
stocks.py search "Apple"
stocks.py search "electric vehicles"

# Limit results
stocks.py search "semiconductor" --limit 10
```

### Historical Data

```bash
# Default: 1 month daily
stocks.py history AAPL

# Custom period and interval
stocks.py history TSLA --period 1y --interval 1d
stocks.py history MSFT --period 3mo --interval 1wk
stocks.py history NVDA --period 5d --interval 1h
```

### Generate Charts

```bash
# Default: 6-month candlestick, transparent background
stocks.py chart AAPL

# White background
stocks.py chart TSLA --background white

# Black background
stocks.py chart MSFT --background black

# Line chart
stocks.py chart NVDA --type line

# Custom options
stocks.py chart AMD --period 1y --width 1400 --height 900 --ma 20 50 200 --output amd.png
```

## Command Options

### Quote Command

| Option | Description |
|--------|-------------|
| `symbol` | Stock ticker symbol (required) |
| `--signals`, `-s` | Include trading signals analysis |

### Search Command

| Option | Default | Description |
|--------|---------|-------------|
| `query` | required | Company name to search |
| `--limit`, `-l` | 5 | Maximum results to return |

### History Command

| Option | Default | Description |
|--------|---------|-------------|
| `symbol` | required | Stock ticker symbol |
| `--period`, `-p` | 1mo | Period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max |
| `--interval`, `-i` | 1d | Interval: 1m, 5m, 15m, 1h, 1d, 1wk, 1mo |

### Chart Command

| Option | Default | Description |
|--------|---------|-------------|
| `symbol` | required | Stock ticker symbol |
| `--period`, `-p` | 6mo | Data period |
| `--type`, `-t` | candlestick | Chart type: candlestick, line |
| `--output`, `-o` | auto | Output file path |
| `--width` | 1200 | Width in pixels |
| `--height` | 800 | Height in pixels |
| `--ma` | 20 50 200 | Moving average periods |
| `--background`, `-b` | transparent | Background: transparent, white, black |

## Moving Averages

| Indicator | Period | Use Case |
|-----------|--------|----------|
| SMA 20 | 20 days | Short-term trend |
| SMA 50 | 50 days | Medium-term trend |
| SMA 200 | 200 days | Long-term trend |
| EMA 9 | 9 days | Fast momentum |
| EMA 21 | 21 days | Medium momentum |

## Trading Signals

| Signal | Description |
|--------|-------------|
| Golden Cross | 50-day SMA crosses above 200-day SMA (bullish) |
| Death Cross | 50-day SMA crosses below 200-day SMA (bearish) |
| Bullish Alignment | Price > SMA20 > SMA50 > SMA200 |
| Bearish Alignment | Price < SMA20 < SMA50 < SMA200 |
| EMA Crossovers | 9-day EMA crosses 21-day EMA |

## Agent Skill

This project includes a `SKILL.md` file for use with AI coding agents.

### Installation

```bash
# Create skills directory
mkdir -p /path/to/agent/skills/stocks

# Copy skill files
cp SKILL.md /path/to/agent/skills/stocks/
cp -r scripts/ /path/to/agent/skills/stocks/

# Ensure stocks.py is in PATH
cp scripts/stocks.py ~/.local/bin/
chmod +x ~/.local/bin/stocks.py
```

The agent reads `SKILL.md` to understand available commands, parameters, and how to interpret stock data.

## Ticker Symbol Reference

Beyond stocks, yfinance supports indexes, commodities, currencies, and crypto using special symbol patterns.

### Major US Indexes

| Symbol | Name |
|--------|------|
| `^DJI` | Dow Jones Industrial Average |
| `^GSPC` | S&P 500 |
| `^IXIC` | NASDAQ Composite |
| `^RUT` | Russell 2000 |
| `^VIX` | CBOE Volatility Index |
| `^TNX` | 10-Year Treasury Yield |

### International Indexes

| Symbol | Name |
|--------|------|
| `^FTSE` | FTSE 100 (UK) |
| `^GDAXI` | DAX (Germany) |
| `^N225` | Nikkei 225 (Japan) |
| `^HSI` | Hang Seng (Hong Kong) |

### Commodities (Futures)

#### Energy
| Symbol | Name |
|--------|------|
| `CL=F` | WTI Crude Oil |
| `BZ=F` | Brent Crude Oil |
| `NG=F` | Natural Gas |
| `RB=F` | Gasoline (RBOB) |
| `HO=F` | Heating Oil |

#### Metals
| Symbol | Name |
|--------|------|
| `GC=F` | Gold |
| `SI=F` | Silver |
| `HG=F` | Copper |
| `PL=F` | Platinum |
| `PA=F` | Palladium |

#### Agriculture
| Symbol | Name |
|--------|------|
| `ZC=F` | Corn |
| `ZW=F` | Wheat |
| `ZS=F` | Soybeans |
| `KC=F` | Coffee |
| `SB=F` | Sugar |
| `CC=F` | Cocoa |
| `CT=F` | Cotton |
| `LC=F` | Live Cattle |
| `LH=F` | Lean Hogs |

### Currencies

| Symbol | Name |
|--------|------|
| `EURUSD=X` | Euro / US Dollar |
| `GBPUSD=X` | British Pound / US Dollar |
| `USDJPY=X` | US Dollar / Japanese Yen |
| `DX-Y.NYB` | US Dollar Index (DXY) |

### Cryptocurrencies

| Symbol | Name |
|--------|------|
| `BTC-USD` | Bitcoin |
| `ETH-USD` | Ethereum |
| `SOL-USD` | Solana |

### Symbol Patterns

| Type | Pattern | Example |
|------|---------|---------|
| Stocks | Plain symbol | `AAPL`, `TSLA` |
| Indexes | `^` prefix | `^DJI`, `^GSPC` |
| Futures | `=F` suffix | `CL=F`, `GC=F` |
| Currencies | `=X` suffix | `EURUSD=X` |
| Crypto | `-USD` suffix | `BTC-USD` |

## Data Source

- **Provider**: Yahoo Finance (via yfinance library)
- **Coverage**: US and international exchanges
- **Real-time**: ~15 minute delay for free tier
- **Historical**: Daily data back to IPO for most stocks
