#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "yfinance>=0.2.0",
#     "pandas>=2.0.0",
#     "requests>=2.31.0",
#     "matplotlib>=3.7.0",
# ]
# ///
"""
yfinance CLI - Stock market data and charting tool

Commands:
    quote   - Get stock quote with moving averages and signals
    search  - Search for ticker symbols by company name
    history - Get historical OHLCV data
    chart   - Generate PNG chart with transparent background
"""

import argparse
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

import yfinance as yf
import pandas as pd
import requests


# --- Quote Command ---

def get_quote(symbol: str, include_signals: bool = False) -> Dict[str, Any]:
    """Get stock quote with moving averages and optional signals."""
    ticker = yf.Ticker(symbol)
    info = ticker.info

    if not info or info.get("regularMarketPrice") is None:
        return {"error": f"No data found for symbol: {symbol}"}

    # Get quote timestamp
    market_time = info.get("regularMarketTime")
    if market_time:
        quote_timestamp = datetime.fromtimestamp(market_time).strftime("%Y-%m-%d %H:%M:%S")
    else:
        quote_timestamp = None

    # Basic quote data
    quote = {
        "symbol": symbol.upper(),
        "company_name": info.get("longName", "N/A"),
        "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "dividend_yield": info.get("dividendYield"),
        "52_week_high": info.get("fiftyTwoWeekHigh"),
        "52_week_low": info.get("fiftyTwoWeekLow"),
        "volume": info.get("volume"),
        "avg_volume": info.get("averageVolume"),
        "beta": info.get("beta"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "quote_time": quote_timestamp,
    }

    # Get historical data for moving averages
    hist = ticker.history(period="1y")
    if len(hist) >= 20:
        prices = hist["Close"]
        current_price = quote["current_price"]

        # Calculate moving averages
        ma_data = {}
        for period, name in [(20, "SMA_20"), (50, "SMA_50"), (200, "SMA_200")]:
            if len(prices) >= period:
                ma_value = prices.rolling(window=period).mean().iloc[-1]
                ma_data[name] = {
                    "value": round(ma_value, 2),
                    "position": "above" if current_price > ma_value else "below",
                    "distance_pct": round((current_price - ma_value) / ma_value * 100, 2),
                }

        # EMA
        for span, name in [(9, "EMA_9"), (21, "EMA_21")]:
            if len(prices) >= span:
                ema_value = prices.ewm(span=span).mean().iloc[-1]
                ma_data[name] = {
                    "value": round(ema_value, 2),
                    "position": "above" if current_price > ema_value else "below",
                }

        quote["moving_averages"] = ma_data

        # Detect signals if requested
        if include_signals and len(hist) >= 200:
            signals = detect_signals(prices, current_price)
            quote["signals"] = signals

    return quote


def detect_signals(prices: pd.Series, current_price: float) -> Dict[str, Any]:
    """Detect trading signals from price data."""
    signals = {
        "detected": [],
        "trend_alignment": "mixed",
        "recommendation": "wait",
    }

    sma_20 = prices.rolling(window=20).mean()
    sma_50 = prices.rolling(window=50).mean()
    sma_200 = prices.rolling(window=200).mean()
    ema_9 = prices.ewm(span=9).mean()
    ema_21 = prices.ewm(span=21).mean()

    current_20 = sma_20.iloc[-1]
    current_50 = sma_50.iloc[-1]
    current_200 = sma_200.iloc[-1]
    prev_50 = sma_50.iloc[-2]
    prev_200 = sma_200.iloc[-2]

    # Golden Cross / Death Cross
    if current_50 > current_200 and prev_50 <= prev_200:
        signals["detected"].append({"type": "golden_cross", "strength": "strong_bullish"})
    elif current_50 < current_200 and prev_50 >= prev_200:
        signals["detected"].append({"type": "death_cross", "strength": "strong_bearish"})

    # Trend alignment
    bullish = current_price > current_20 > current_50 > current_200
    bearish = current_price < current_20 < current_50 < current_200

    if bullish:
        signals["trend_alignment"] = "strong_bullish"
        signals["detected"].append({"type": "bullish_alignment", "strength": "strong_bullish"})
    elif bearish:
        signals["trend_alignment"] = "strong_bearish"
        signals["detected"].append({"type": "bearish_alignment", "strength": "strong_bearish"})

    # EMA crossover
    current_ema9 = ema_9.iloc[-1]
    current_ema21 = ema_21.iloc[-1]
    prev_ema9 = ema_9.iloc[-2]
    prev_ema21 = ema_21.iloc[-2]

    if current_ema9 > current_ema21 and prev_ema9 <= prev_ema21:
        signals["detected"].append({"type": "ema_bullish_crossover", "strength": "moderate_bullish"})
    elif current_ema9 < current_ema21 and prev_ema9 >= prev_ema21:
        signals["detected"].append({"type": "ema_bearish_crossover", "strength": "moderate_bearish"})

    # Recommendation
    bullish_count = sum(1 for s in signals["detected"] if "bullish" in s.get("strength", ""))
    bearish_count = sum(1 for s in signals["detected"] if "bearish" in s.get("strength", ""))

    if bullish_count > bearish_count:
        signals["recommendation"] = "consider_buy"
    elif bearish_count > bullish_count:
        signals["recommendation"] = "avoid_or_sell"

    return signals


def format_quote(quote: Dict[str, Any]) -> str:
    """Format quote data for display."""
    if "error" in quote:
        return f"Error: {quote['error']}"

    lines = [
        f"\n{'='*60}",
        f"  {quote['symbol']} - {quote.get('company_name', 'N/A')}",
        f"{'='*60}",
        "",
        "  PRICE & VALUATION",
        f"  Current Price:    ${quote.get('current_price', 'N/A'):,.2f}" if quote.get('current_price') else "  Current Price:    N/A",
        f"  Market Cap:       ${quote.get('market_cap', 0):,.0f}" if quote.get('market_cap') else "  Market Cap:       N/A",
        f"  P/E Ratio:        {quote.get('pe_ratio', 'N/A'):.2f}" if quote.get('pe_ratio') else "  P/E Ratio:        N/A",
        f"  Forward P/E:      {quote.get('forward_pe', 'N/A'):.2f}" if quote.get('forward_pe') else "  Forward P/E:      N/A",
        f"  Dividend Yield:   {quote.get('dividend_yield', 0)*100:.2f}%" if quote.get('dividend_yield') else "  Dividend Yield:   N/A",
        "",
        "  52-WEEK RANGE",
        f"  High:             ${quote.get('52_week_high', 'N/A'):,.2f}" if quote.get('52_week_high') else "  High:             N/A",
        f"  Low:              ${quote.get('52_week_low', 'N/A'):,.2f}" if quote.get('52_week_low') else "  Low:              N/A",
        "",
        "  VOLUME",
        f"  Volume:           {quote.get('volume', 0):,}" if quote.get('volume') else "  Volume:           N/A",
        f"  Avg Volume:       {quote.get('avg_volume', 0):,}" if quote.get('avg_volume') else "  Avg Volume:       N/A",
        "",
        "  CLASSIFICATION",
        f"  Sector:           {quote.get('sector', 'N/A')}",
        f"  Industry:         {quote.get('industry', 'N/A')}",
        f"  Beta:             {quote.get('beta', 'N/A'):.2f}" if quote.get('beta') else "  Beta:             N/A",
    ]

    # Moving averages
    if "moving_averages" in quote:
        lines.extend(["", "  MOVING AVERAGES"])
        for ma_name, ma_info in quote["moving_averages"].items():
            position = ma_info.get("position", "")
            distance = ma_info.get("distance_pct", "")
            distance_str = f" ({distance:+.2f}%)" if distance is not None and distance != "" else ""
            lines.append(f"  {ma_name:12}  ${ma_info['value']:>10,.2f}  [{position.upper()}]{distance_str}")

    # Signals
    if "signals" in quote:
        signals = quote["signals"]
        lines.extend(["", "  TRADING SIGNALS"])
        lines.append(f"  Trend Alignment:  {signals.get('trend_alignment', 'mixed').upper()}")
        lines.append(f"  Recommendation:   {signals.get('recommendation', 'wait').upper()}")
        if signals.get("detected"):
            lines.append("  Detected:")
            for sig in signals["detected"]:
                lines.append(f"    - {sig['type']} ({sig['strength']})")

    # Quote timestamp at bottom
    if quote.get("quote_time"):
        lines.append(f"\n  Quote: {quote['quote_time']}")

    lines.append(f"\n{'='*60}\n")
    return "\n".join(lines)


# --- Search Command ---

def search_ticker(query: str, limit: int = 5) -> Dict[str, Any]:
    """Search for ticker symbols by company name."""
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    params = {"q": query, "quotes_count": limit, "country": "United States"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        quotes = response.json().get("quotes", [])

        results = []
        for quote in quotes[:limit]:
            results.append({
                "symbol": quote.get("symbol", "N/A"),
                "name": quote.get("longname") or quote.get("shortname", "N/A"),
                "exchange": quote.get("exchange", "N/A"),
                "type": quote.get("quoteType", "N/A"),
            })

        return {"query": query, "count": len(results), "results": results}

    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}


def format_search(data: Dict[str, Any]) -> str:
    """Format search results for display."""
    if "error" in data:
        return f"Error: {data['error']}"

    lines = [f"\nSearch results for '{data['query']}': {data['count']} found\n"]

    if not data["results"]:
        lines.append("  No results found.")
    else:
        lines.append(f"  {'SYMBOL':<10} {'EXCHANGE':<10} {'TYPE':<10} NAME")
        lines.append(f"  {'-'*10} {'-'*10} {'-'*10} {'-'*30}")
        for r in data["results"]:
            lines.append(f"  {r['symbol']:<10} {r['exchange']:<10} {r['type']:<10} {r['name']}")

    lines.append("")
    return "\n".join(lines)


# --- History Command ---

def get_history(symbol: str, period: str = "1mo", interval: str = "1d") -> Dict[str, Any]:
    """Get historical OHLCV data."""
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period, interval=interval)

    if hist.empty:
        return {"error": f"No historical data found for {symbol}"}

    records = []
    for date, row in hist.iterrows():
        records.append({
            "date": date.strftime("%Y-%m-%d"),
            "open": round(row["Open"], 2),
            "high": round(row["High"], 2),
            "low": round(row["Low"], 2),
            "close": round(row["Close"], 2),
            "volume": int(row["Volume"]),
        })

    return {
        "symbol": symbol.upper(),
        "period": period,
        "interval": interval,
        "count": len(records),
        "data": records,
    }


def format_history(data: Dict[str, Any]) -> str:
    """Format history data for display."""
    if "error" in data:
        return f"Error: {data['error']}"

    lines = [
        f"\n{data['symbol']} Historical Data ({data['period']}, {data['interval']})",
        f"Records: {data['count']}\n",
        f"  {'DATE':<12} {'OPEN':>10} {'HIGH':>10} {'LOW':>10} {'CLOSE':>10} {'VOLUME':>14}",
        f"  {'-'*12} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*14}",
    ]

    for rec in data["data"]:
        lines.append(
            f"  {rec['date']:<12} {rec['open']:>10.2f} {rec['high']:>10.2f} "
            f"{rec['low']:>10.2f} {rec['close']:>10.2f} {rec['volume']:>14,}"
        )

    lines.append("")
    return "\n".join(lines)


# --- Chart Command ---

def generate_chart(
    symbol: str,
    period: str = "6mo",
    chart_type: str = "candlestick",
    output: Optional[str] = None,
    width: int = 1200,
    height: int = 800,
    ma_periods: Optional[List[int]] = None,
    background: str = "transparent",
) -> str:
    """Generate PNG chart with configurable background."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    if ma_periods is None:
        ma_periods = [20, 50, 200]

    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period)

    if hist.empty:
        return f"Error: No data found for {symbol}"

    # Color schemes based on background
    if background == "black":
        colors = {
            "price": "#FFFFFF",
            "bullish": "#00FF88",
            "bearish": "#FF6B6B",
            "ma_20": "#FFD93D",
            "ma_50": "#C084FC",
            "ma_200": "#60A5FA",
            "volume_up": "#00FF88",
            "volume_down": "#FF6B6B",
            "grid": "#444444",
            "text": "#FFFFFF",
            "bg": "#000000",
        }
        fig_facecolor = "#000000"
        ax_facecolor = "#000000"
        transparent = False
    elif background == "white":
        colors = {
            "price": "#2C3E50",
            "bullish": "#27AE60",
            "bearish": "#E74C3C",
            "ma_20": "#F39C12",
            "ma_50": "#9B59B6",
            "ma_200": "#3498DB",
            "volume_up": "#27AE60",
            "volume_down": "#E74C3C",
            "grid": "#CCCCCC",
            "text": "#2C3E50",
            "bg": "#FFFFFF",
        }
        fig_facecolor = "#FFFFFF"
        ax_facecolor = "#FFFFFF"
        transparent = False
    else:  # transparent
        colors = {
            "price": "#2C3E50",
            "bullish": "#27AE60",
            "bearish": "#E74C3C",
            "ma_20": "#F39C12",
            "ma_50": "#9B59B6",
            "ma_200": "#3498DB",
            "volume_up": "#27AE60",
            "volume_down": "#E74C3C",
            "grid": "#CCCCCC",
            "text": "#2C3E50",
            "bg": "none",
        }
        fig_facecolor = "none"
        ax_facecolor = "none"
        transparent = True

    # Setup figure
    fig_width = width / 100
    fig_height = height / 100

    if chart_type == "candlestick":
        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(fig_width, fig_height),
            gridspec_kw={"height_ratios": [3, 1]},
            facecolor=fig_facecolor
        )
        ax1.set_facecolor(ax_facecolor)
        ax2.set_facecolor(ax_facecolor)

        # Candlestick chart
        for i in range(len(hist)):
            date = mdates.date2num(hist.index[i])
            open_price = hist["Open"].iloc[i]
            close_price = hist["Close"].iloc[i]
            high_price = hist["High"].iloc[i]
            low_price = hist["Low"].iloc[i]

            color = colors["bullish"] if close_price >= open_price else colors["bearish"]

            # Wick
            ax1.plot([date, date], [low_price, high_price], color=color, linewidth=0.8)
            # Body
            body_bottom = min(open_price, close_price)
            body_height = abs(close_price - open_price)
            ax1.bar(date, body_height, bottom=body_bottom, width=0.6, color=color, edgecolor=color)

        # Volume bars
        volume_colors = [
            colors["volume_up"] if hist["Close"].iloc[i] >= hist["Open"].iloc[i] else colors["volume_down"]
            for i in range(len(hist))
        ]
        ax2.bar(mdates.date2num(hist.index), hist["Volume"], width=0.6, color=volume_colors, alpha=0.7)
        ax2.set_ylabel("Volume", color=colors["text"])
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x/1e6:.1f}M"))
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax2.tick_params(colors=colors["text"])
        ax2.grid(True, alpha=0.3, color=colors["grid"])

    else:  # line chart
        fig, ax1 = plt.subplots(figsize=(fig_width, fig_height), facecolor=fig_facecolor)
        ax1.set_facecolor(ax_facecolor)
        ax1.plot(hist.index, hist["Close"], color=colors["price"], linewidth=2, label="Close")

    # Add moving averages
    ma_colors = {20: colors["ma_20"], 50: colors["ma_50"], 200: colors["ma_200"]}
    for ma_period in ma_periods:
        if len(hist) >= ma_period:
            ma = hist["Close"].rolling(window=ma_period).mean()
            ax1.plot(
                hist.index, ma,
                color=ma_colors.get(ma_period, "#888888"),
                linewidth=1.5,
                label=f"MA {ma_period}",
                alpha=0.8
            )

    # Styling
    ax1.set_title(f"{symbol.upper()} - {period.upper()}", color=colors["text"], fontsize=14, pad=10)
    ax1.set_ylabel("Price ($)", color=colors["text"])
    ax1.tick_params(colors=colors["text"])
    ax1.grid(True, alpha=0.3, color=colors["grid"])

    # Only show legend if there are labeled elements
    handles, _ = ax1.get_legend_handles_labels()
    if handles:
        ax1.legend(loc="upper left", framealpha=0.8)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax1.xaxis.set_major_locator(mdates.AutoDateLocator())

    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha="right", color=colors["text"])
    if chart_type == "candlestick":
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha="right", color=colors["text"])

    plt.tight_layout()

    # Output path
    if output is None:
        output = f"{symbol.lower()}_{period}_{chart_type}.png"

    # Save chart
    fig.savefig(output, format="png", dpi=100, bbox_inches="tight", transparent=transparent,
                facecolor=fig_facecolor if not transparent else "none")
    plt.close(fig)

    return f"Chart saved: {output}"


# --- CLI Entry Point ---

def main():
    parser = argparse.ArgumentParser(
        description="yfinance CLI - Stock market data and charting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # quote command
    quote_parser = subparsers.add_parser("quote", help="Get stock quote with moving averages")
    quote_parser.add_argument("symbol", help="Stock ticker symbol (e.g., AAPL)")
    quote_parser.add_argument("--signals", "-s", action="store_true", help="Include trading signals")

    # search command
    search_parser = subparsers.add_parser("search", help="Search for ticker symbols")
    search_parser.add_argument("query", help="Company name to search")
    search_parser.add_argument("--limit", "-l", type=int, default=5, help="Max results (default: 5)")

    # history command
    history_parser = subparsers.add_parser("history", help="Get historical OHLCV data")
    history_parser.add_argument("symbol", help="Stock ticker symbol")
    history_parser.add_argument("--period", "-p", default="1mo", help="Period: 1d,5d,1mo,3mo,6mo,1y,2y,5y,max (default: 1mo)")
    history_parser.add_argument("--interval", "-i", default="1d", help="Interval: 1m,5m,15m,1h,1d,1wk,1mo (default: 1d)")

    # chart command
    chart_parser = subparsers.add_parser("chart", help="Generate PNG chart")
    chart_parser.add_argument("symbol", help="Stock ticker symbol")
    chart_parser.add_argument("--period", "-p", default="6mo", help="Period (default: 6mo)")
    chart_parser.add_argument("--type", "-t", choices=["candlestick", "line"], default="candlestick", help="Chart type")
    chart_parser.add_argument("--output", "-o", help="Output file path")
    chart_parser.add_argument("--width", type=int, default=1200, help="Width in pixels (default: 1200)")
    chart_parser.add_argument("--height", type=int, default=800, help="Height in pixels (default: 800)")
    chart_parser.add_argument("--ma", nargs="*", type=int, default=[20, 50, 200], help="Moving average periods (omit values to disable)")
    chart_parser.add_argument("--background", "-b", choices=["transparent", "white", "black"], default="transparent", help="Background color (default: transparent)")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "quote":
        data = get_quote(args.symbol, include_signals=args.signals)
        print(format_quote(data))

    elif args.command == "search":
        data = search_ticker(args.query, limit=args.limit)
        print(format_search(data))

    elif args.command == "history":
        data = get_history(args.symbol, period=args.period, interval=args.interval)
        print(format_history(data))

    elif args.command == "chart":
        result = generate_chart(
            args.symbol,
            period=args.period,
            chart_type=args.type,
            output=args.output,
            width=args.width,
            height=args.height,
            ma_periods=args.ma,
            background=args.background,
        )
        print(result)


if __name__ == "__main__":
    main()
