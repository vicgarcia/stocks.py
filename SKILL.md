---
name: stocks
description: Get stock market data from Yahoo Finance. Use when the user asks about stock prices, quotes, company valuations, moving averages, trading signals, historical data, or wants to generate stock charts. Supports any publicly traded stock via ticker symbol.
compatibility: Requires 'stocks.py' script in PATH.
---

# Stock Market Data Tool

Get stock quotes, historical data, and generate charts using the `stocks.py` CLI powered by Yahoo Finance.

## Commands Reference

### Stock Quote
```bash
stocks.py quote AAPL
stocks.py quote TSLA --signals
stocks.py quote MSFT -s
```

Returns:
- Current price
- Market cap
- P/E ratio (trailing and forward)
- Dividend yield
- 52-week high/low
- Volume (current and average)
- Beta
- Sector and industry
- Moving averages (SMA 20/50/200, EMA 9/21)
- Position relative to each MA (above/below with % distance)

### Quote with Trading Signals
```bash
stocks.py quote NVDA --signals
stocks.py quote AMD -s
```

Additional signal data includes:
- Trend alignment (strong bullish/bearish/mixed)
- Recommendation (consider_buy/avoid_or_sell/wait)
- Detected signals:
  - Golden Cross (50-day crosses above 200-day SMA)
  - Death Cross (50-day crosses below 200-day SMA)
  - Bullish/Bearish alignment (price > MA20 > MA50 > MA200)
  - EMA crossovers (9-day EMA crosses 21-day EMA)

### Search for Tickers
```bash
stocks.py search "Apple"
stocks.py search "electric vehicles" --limit 10
stocks.py search "semiconductor" -l 8
```

Returns:
- Ticker symbol
- Company name
- Exchange
- Quote type (EQUITY, ETF, etc.)

### Historical Data
```bash
# Default: 1 month of daily data
stocks.py history AAPL

# 1 year of daily data
stocks.py history TSLA --period 1y

# 3 months of weekly data
stocks.py history MSFT --period 3mo --interval 1wk

# 5 days of hourly data
stocks.py history NVDA --period 5d --interval 1h
```

Period options: `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `max`
Interval options: `1m`, `5m`, `15m`, `1h`, `1d`, `1wk`, `1mo`

Returns OHLCV data:
- Date
- Open, High, Low, Close prices
- Volume

### Generate Charts
```bash
# Default: 6-month candlestick with transparent background
stocks.py chart AAPL

# Line chart
stocks.py chart TSLA --type line

# Custom period
stocks.py chart MSFT --period 1y

# White background (good for documents)
stocks.py chart NVDA --background white

# Black background (good for dark themes)
stocks.py chart AMD --background black

# Custom dimensions
stocks.py chart GOOGL --width 1600 --height 1000

# Custom moving averages
stocks.py chart META --ma 9 21 50

# Full options
stocks.py chart AAPL --period 1y --type candlestick --background white --width 1400 --height 900 --ma 20 50 200 --output aapl_chart.png
```

Chart features:
- Candlestick or line chart types
- Moving average overlays (customizable periods)
- Volume subplot (candlestick mode)
- Transparent, white, or black backgrounds
- Auto-contrasting colors for each background

## Example Workflows

### Quick Stock Check
```bash
stocks.py quote AAPL
```

### Research a Company
```bash
# Find the ticker
stocks.py search "Tesla"

# Get detailed quote with signals
stocks.py quote TSLA --signals

# View historical performance
stocks.py history TSLA --period 1y

# Generate chart for analysis
stocks.py chart TSLA --period 1y --background white
```

### Compare Stocks
```bash
for ticker in AAPL MSFT GOOGL; do
  stocks.py quote $ticker
done
```

### Trading Signal Analysis
```bash
# Check signals for multiple stocks
stocks.py quote AAPL --signals
stocks.py quote NVDA --signals
stocks.py quote AMD --signals
```

### Generate Charts for Presentation
```bash
# White background for documents/slides
stocks.py chart AAPL --background white --width 1400 --height 900

# Black background for dark-themed presentations
stocks.py chart TSLA --background black

# Transparent for overlay on any background
stocks.py chart MSFT --background transparent
```

### Historical Analysis
```bash
# Get weekly data for trend analysis
stocks.py history SPY --period 2y --interval 1wk

# Get daily data for recent moves
stocks.py history QQQ --period 3mo
```

## Understanding the Output

### Moving Averages
| Indicator | Description | Use Case |
|-----------|-------------|----------|
| SMA 20 | 20-day Simple Moving Average | Short-term trend |
| SMA 50 | 50-day Simple Moving Average | Medium-term trend |
| SMA 200 | 200-day Simple Moving Average | Long-term trend |
| EMA 9 | 9-day Exponential Moving Average | Fast signal |
| EMA 21 | 21-day Exponential Moving Average | Medium signal |

### Trading Signals
| Signal | Meaning | Implication |
|--------|---------|-------------|
| Golden Cross | 50-day SMA crosses above 200-day | Bullish reversal |
| Death Cross | 50-day SMA crosses below 200-day | Bearish reversal |
| Bullish Alignment | Price > MA20 > MA50 > MA200 | Strong uptrend |
| Bearish Alignment | Price < MA20 < MA50 < MA200 | Strong downtrend |
| EMA Bullish Crossover | 9-day EMA crosses above 21-day | Short-term bullish |
| EMA Bearish Crossover | 9-day EMA crosses below 21-day | Short-term bearish |

### Trend Alignment
| Value | Meaning |
|-------|---------|
| strong_bullish | All MAs aligned bullishly |
| strong_bearish | All MAs aligned bearishly |
| mixed | No clear alignment |

### Recommendation
| Value | Interpretation |
|-------|----------------|
| consider_buy | More bullish than bearish signals |
| avoid_or_sell | More bearish than bullish signals |
| wait | No clear signal dominance |

## Ticker Symbol Reference

### Major US Indexes
| Symbol | Name |
|--------|------|
| `^DJI` | Dow Jones Industrial Average |
| `^GSPC` | S&P 500 |
| `^IXIC` | NASDAQ Composite |
| `^RUT` | Russell 2000 |
| `^VIX` | CBOE Volatility Index (VIX) |
| `^TNX` | 10-Year Treasury Yield |
| `^TYX` | 30-Year Treasury Yield |

### International Indexes
| Symbol | Name |
|--------|------|
| `^FTSE` | FTSE 100 (UK) |
| `^GDAXI` | DAX (Germany) |
| `^N225` | Nikkei 225 (Japan) |
| `^HSI` | Hang Seng (Hong Kong) |
| `^STOXX50E` | Euro Stoxx 50 |

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
| `USDCAD=X` | US Dollar / Canadian Dollar |
| `AUDUSD=X` | Australian Dollar / US Dollar |
| `DX-Y.NYB` | US Dollar Index (DXY) |

### Cryptocurrencies
| Symbol | Name |
|--------|------|
| `BTC-USD` | Bitcoin |
| `ETH-USD` | Ethereum |
| `SOL-USD` | Solana |
| `XRP-USD` | Ripple |
| `DOGE-USD` | Dogecoin |

### Symbol Patterns
| Type | Pattern | Example |
|------|---------|---------|
| Stocks | Plain symbol | `AAPL`, `TSLA` |
| Indexes | `^` prefix | `^DJI`, `^GSPC` |
| Futures | `=F` suffix | `CL=F`, `GC=F` |
| Currencies | `=X` suffix | `EURUSD=X` |
| Crypto | `-USD` suffix | `BTC-USD` |

## Tips

- Use `--signals` flag for trading analysis, omit for quick price checks
- Use `search` when you don't know the exact ticker symbol
- Chart backgrounds: `white` for light docs, `black` for dark themes, `transparent` for overlays
- Historical intervals: use smaller intervals (1h, 15m) only with shorter periods (5d, 1mo)
- Moving averages require sufficient historical data (200+ days for MA 200)
- Quote timestamps are from the last market data update, not current time
