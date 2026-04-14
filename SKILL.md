---
name: yfinance
description: Get stock market data from Yahoo Finance. Use when the user asks about stock prices, quotes, company valuations, moving averages, trading signals, historical data, stock charts, latest news, analyst recommendations, or fundamental health scores. Supports any publicly traded stock via ticker symbol.
compatibility: Requires uv or yfinance.py in PATH.
---

# Stock Market Data Tool

Get stock quotes, news, analyst recommendations, fundamental health scores, historical data, and charts using the `yfinance.py` CLI powered by Yahoo Finance.

## Invocation

If `yfinance.py` is installed in PATH:
```bash
yfinance.py <command> [args]
```

Or run directly without installing:
```bash
uv run --script /path/to/skill/scripts/yfinance.py <command> [args]
```

Examples in this document use `yfinance.py` as shorthand for either invocation form above.

## Commands Reference

### Stock Quote
```bash
yfinance.py quote AAPL
yfinance.py quote TSLA --signals
yfinance.py quote MSFT -s
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
yfinance.py quote NVDA --signals
yfinance.py quote AMD -s
```

Additional signal data includes:
- Trend alignment (strong bullish/bearish/mixed)
- Recommendation (consider_buy/avoid_or_sell/wait)
- Detected signals:
  - Golden Cross (50-day crosses above 200-day SMA)
  - Death Cross (50-day crosses below 200-day SMA)
  - Bullish/Bearish alignment (price > MA20 > MA50 > MA200)
  - EMA crossovers (9-day EMA crosses 21-day EMA)

### Generate Charts
```bash
# Default: 6-month candlestick, no moving averages
yfinance.py chart AAPL

# Line chart
yfinance.py chart TSLA --type line

# Custom period
yfinance.py chart MSFT --period 1y

# White background (good for documents)
yfinance.py chart NVDA --background white

# Black background (good for dark themes)
yfinance.py chart AMD --background black

# Custom dimensions
yfinance.py chart GOOGL --width 1600 --height 1000

# Custom moving averages
yfinance.py chart META --ma 9 21 50

# Full options
yfinance.py chart AAPL --period 1y --type candlestick --background white --width 1400 --height 900 --ma 20 50 200 --output aapl_chart.png
```

Chart features:
- Candlestick or line chart types
- Moving average overlays (customizable periods)
- Volume subplot (candlestick mode)
- Transparent, white, or black backgrounds
- Auto-contrasting colors for each background

### Search for Tickers
```bash
yfinance.py search "Apple"
yfinance.py search "electric vehicles" --limit 10
yfinance.py search "semiconductor" -l 8
```

Returns:
- Ticker symbol
- Company name
- Exchange
- Quote type (EQUITY, ETF, etc.)

### Latest News
```bash
# News for a specific ticker
yfinance.py news AAPL
yfinance.py news TSLA --count 10

# General market/topic news
yfinance.py news "oil prices"
yfinance.py news "Federal Reserve interest rates"
yfinance.py news "semiconductor sector"

# Show full article summary
yfinance.py news NVDA --summary
yfinance.py news "AI chips" -s -n 3
```

Returns for each article:
- Headline
- Publisher and publish timestamp
- Article URL
- Full summary paragraph (with `--summary`)

Options:
| Option | Default | Description |
|--------|---------|-------------|
| `query` | required | Ticker symbol or any search query string |
| `--count`, `-n` | 5 | Number of articles to return |
| `--summary`, `-s` | off | Show full summary paragraph |

### Historical Data
```bash
# Default: 1 month of daily data
yfinance.py history AAPL

# 1 year of daily data
yfinance.py history TSLA --period 1y

# 3 months of weekly data
yfinance.py history MSFT --period 3mo --interval 1wk

# 5 days of hourly data
yfinance.py history NVDA --period 5d --interval 1h
```

Period options: `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `max`
Interval options: `1m`, `5m`, `15m`, `1h`, `1d`, `1wk`, `1mo`

Returns OHLCV data:
- Date
- Open, High, Low, Close prices
- Volume

### Fundamental Health Score
```bash
# Scored four-pillar report
yfinance.py fundamentals AAPL

# Raw numbers table (no scoring)
yfinance.py fundamentals GOOGL --raw

# JSON output for agent/LLM use
yfinance.py fundamentals META --json
```

Returns a **0–100 Health Score** built from four pillars (each 0–25):

| Pillar | Metrics |
|--------|---------|
| **Profitability** | Gross Margin, Net Margin, Operating Margin (all TTM), Margin Trend vs 3yr avg |
| **Growth** | Revenue CAGR (3yr), Net Income CAGR (3yr), YoY Acceleration bonus/penalty |
| **Financial Health** | Debt-to-Equity, Current Ratio, Debt Trend (3yr) |
| **Cash Generation** | FCF Margin (TTM), FCF Consistency (3yr), FCF Quality (FCF/Net Income) |

Each metric shows a dot meter (`●●●●○`) indicating score relative to its full-score threshold. Pillar scores and total score are shown numerically.

Scoring thresholds (full score):
- Gross Margin ≥ 50%, Net Margin ≥ 20%, Operating Margin ≥ 25%
- Revenue / Net Income CAGR ≥ 15%
- Debt-to-Equity ≤ 0.5, Current Ratio ≥ 2.0
- FCF Margin ≥ 20%, FCF Quality (FCF/NI) ≥ 0.8

Options:
| Option | Description |
|--------|-------------|
| `symbol` | Stock ticker symbol (required) |
| `--raw` | Print underlying numbers table without scoring |
| `--json` | Output everything as JSON for agent/LLM consumption |

### Analyst Recommendations
```bash
# Current consensus + recent rating changes
yfinance.py recommendations AAPL

# Extended history
yfinance.py recommendations TSLA --history 6
yfinance.py recommendations NVDA -H 1
```

Returns:
- **Consensus breakdown** — strongBuy / buy / hold / sell / strongSell counts for current month and prior 2 months, with BUY / HOLD/MIXED / SELL verdict
- **Recent rating changes** — per-firm actions with FromGrade → ToGrade, price targets with direction arrows, and action label (upgraded / downgraded / maintains)

Consensus verdict logic:
- `strongBuy + buy > 60%` of total → **BUY**
- `strongSell + sell > 20%` of total → **SELL**
- Otherwise → **HOLD/MIXED**

Options:
| Option | Default | Description |
|--------|---------|-------------|
| `symbol` | required | Stock ticker symbol |
| `--history`, `-H` | 3 | Months of rating change history to show |

## Example Workflows

### Quick Stock Check
```bash
yfinance.py quote AAPL
```

### Full Company Analysis (Layered Stack)
```bash
# Layer 1: Is the business fundamentally healthy? (objective, backward-looking)
yfinance.py fundamentals AAPL

# Layer 2: What do analysts think? (forward-looking consensus)
yfinance.py recommendations AAPL

# Layer 3: What is happening right now? (real-time context)
yfinance.py news AAPL
```

### Agent Analysis Pipeline (JSON)
```bash
# All three outputs as JSON for an LLM to synthesize
yfinance.py fundamentals AAPL --json
yfinance.py recommendations AAPL
yfinance.py news AAPL --count 10
```

### Screen Stocks by Health Score
```bash
# Compare fundamentals across multiple tickers
for ticker in AAPL MSFT GOOGL META AMZN; do
  yfinance.py fundamentals $ticker
done
```

### Research a Company
```bash
# Find the ticker
yfinance.py search "Tesla"

# Get detailed quote with signals
yfinance.py quote TSLA --signals

# Check fundamental health
yfinance.py fundamentals TSLA

# View analyst consensus
yfinance.py recommendations TSLA

# Latest news
yfinance.py news TSLA

# View historical performance
yfinance.py history TSLA --period 1y

# Generate chart for analysis
yfinance.py chart TSLA --period 1y --background white
```

### Market / Topic News
```bash
yfinance.py news "Federal Reserve"
yfinance.py news "oil prices" --count 10
yfinance.py news "semiconductor tariffs" --summary
```

### Compare Stocks
```bash
for ticker in AAPL MSFT GOOGL; do
  yfinance.py quote $ticker
done
```

### Trading Signal Analysis
```bash
# Check signals for multiple stocks
yfinance.py quote AAPL --signals
yfinance.py quote NVDA --signals
yfinance.py quote AMD --signals
```

### Generate Charts for Presentation
```bash
# White background for documents/slides
yfinance.py chart AAPL --background white --width 1400 --height 900

# Black background for dark-themed presentations
yfinance.py chart TSLA --background black

# Transparent for overlay on any background
yfinance.py chart MSFT --background transparent
```

### Historical Analysis
```bash
# Get weekly data for trend analysis
yfinance.py history SPY --period 2y --interval 1wk

# Get daily data for recent moves
yfinance.py history QQQ --period 3mo
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
