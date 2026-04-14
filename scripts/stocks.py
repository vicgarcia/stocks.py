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
    quote           - Get stock quote with moving averages and signals
    search          - Search for ticker symbols by company name
    history         - Get historical OHLCV data
    chart           - Generate PNG chart with white background (default)
    news            - Get latest news for a ticker or any search query
    recommendations - Analyst consensus and recent rating changes
    fundamentals    - Four-pillar fundamental health score (0-100)
"""

import argparse
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

import scripts.stocks as yf
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
    interval: str = "1d",
    chart_type: str = "candlestick",
    output: Optional[str] = None,
    width: int = 1200,
    height: int = 800,
    ma_periods: Optional[List[int]] = None,
    background: str = "white",
) -> str:
    """Generate PNG chart with configurable background."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    if ma_periods is None:
        ma_periods = [20, 50, 200]

    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period, interval=interval)

    if hist.empty:
        return f"Error: No data found for {symbol}"

    # Detect intraday data and compute bar width + date format accordingly
    if len(hist) > 1:
        bar_delta_days = (hist.index[1] - hist.index[0]).total_seconds() / 86400
    else:
        bar_delta_days = 1.0
    bar_width = bar_delta_days * 0.8
    is_intraday = bar_delta_days < 1.0
    date_fmt = mdates.DateFormatter("%H:%M") if is_intraday else mdates.DateFormatter("%b %d")

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
            ax1.bar(date, body_height, bottom=body_bottom, width=bar_width, color=color, edgecolor=color)

        # Volume bars
        volume_colors = [
            colors["volume_up"] if hist["Close"].iloc[i] >= hist["Open"].iloc[i] else colors["volume_down"]
            for i in range(len(hist))
        ]
        ax2.bar(mdates.date2num(hist.index), hist["Volume"], width=bar_width, color=volume_colors, alpha=0.7)
        ax2.set_ylabel("Volume", color=colors["text"])
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x/1e6:.1f}M"))
        ax2.xaxis.set_major_formatter(date_fmt)
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
    ax1.xaxis.set_major_formatter(date_fmt)
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


# --- News Command ---

def get_news(query: str, count: int = 5) -> Dict[str, Any]:
    """Get news articles for a ticker symbol or general search query."""
    try:
        results = yf.Search(query, news_count=count).news
    except Exception as e:
        return {"error": f"News fetch failed: {str(e)}"}

    if not results:
        return {"query": query, "count": 0, "articles": []}

    articles = []
    for item in results[:count]:
        source = item.get("publisher", "Unknown")

        url = item.get("link", "")

        pub_ts = item.get("providerPublishTime") or item.get("pubDate")
        if isinstance(pub_ts, (int, float)):
            try:
                pub_date = datetime.fromtimestamp(pub_ts).strftime("%b %d %Y, %-I:%M %p")
            except Exception:
                pub_date = str(pub_ts)
        else:
            pub_date = str(pub_ts) if pub_ts else ""

        articles.append({
            "title": item.get("title", "No title"),
            "summary": item.get("summary", ""),
            "pub_date": pub_date,
            "source": source,
            "url": url,
        })

    return {"query": query, "count": len(articles), "articles": articles}


def format_news(data: Dict[str, Any], full_summary: bool = False) -> str:
    """Format news articles for display."""
    if "error" in data:
        return f"Error: {data['error']}"

    query = data["query"]
    count = data["count"]
    sep = "=" * 60

    lines = [
        f"\n{query.upper()}  Latest News  ({count} articles)",
        sep,
    ]

    if not data["articles"]:
        lines.append("\n  No news articles found.")
    else:
        for i, article in enumerate(data["articles"], 1):
            lines.append("")
            lines.append(f"[{i}] {article['title']}")
            lines.append(f"    {article['source']} · {article['pub_date']}")

            summary = article.get("summary", "")
            if summary:
                if full_summary:
                    # Wrap long summaries at ~72 chars
                    words = summary.split()
                    line_buf, wrapped = [], []
                    for word in words:
                        if sum(len(w) + 1 for w in line_buf) + len(word) > 72:
                            wrapped.append("    " + " ".join(line_buf))
                            line_buf = [word]
                        else:
                            line_buf.append(word)
                    if line_buf:
                        wrapped.append("    " + " ".join(line_buf))
                    lines.extend(wrapped)
                else:
                    truncated = summary[:120] + "..." if len(summary) > 120 else summary
                    lines.append(f"    {truncated}")

            if article["url"]:
                lines.append(f"    {article['url']}")

    lines.append(f"\n{sep}\n")
    return "\n".join(lines)


# --- Recommendations Command ---

def get_recommendations(symbol: str, history_months: int = 3) -> Dict[str, Any]:
    """Get analyst consensus and recent rating changes."""
    ticker = yf.Ticker(symbol)

    # Consensus summary (current + prior 2 months)
    consensus_rows = []
    try:
        summary = ticker.recommendations_summary
        if summary is not None and not summary.empty:
            for _, row in summary.iterrows():
                period = row.get("period", "")
                strong_buy  = int(row.get("strongBuy",  0))
                buy         = int(row.get("buy",        0))
                hold        = int(row.get("hold",       0))
                sell        = int(row.get("sell",       0))
                strong_sell = int(row.get("strongSell", 0))
                total = strong_buy + buy + hold + sell + strong_sell
                if total > 0:
                    bull_pct = (strong_buy + buy) / total
                    bear_pct = (strong_sell + sell) / total
                    if bull_pct > 0.60:
                        label = "BUY"
                    elif bear_pct > 0.20:
                        label = "SELL"
                    else:
                        label = "HOLD/MIXED"
                else:
                    label = "N/A"
                consensus_rows.append({
                    "period": period,
                    "strong_buy": strong_buy,
                    "buy": buy,
                    "hold": hold,
                    "sell": sell,
                    "strong_sell": strong_sell,
                    "total": total,
                    "label": label,
                })
    except Exception:
        pass

    # Upgrades/downgrades
    rating_changes = []
    try:
        ud = ticker.upgrades_downgrades
        if ud is not None and not ud.empty:
            # Filter to requested months window
            cutoff = pd.Timestamp.now() - pd.DateOffset(months=history_months)
            ud = ud[ud.index >= cutoff]
            ud = ud.sort_index(ascending=False)

            for date, row in ud.iterrows():
                firm        = row.get("Firm", "")
                from_grade  = row.get("FromGrade", "")
                to_grade    = row.get("ToGrade", "")
                action      = row.get("Action", "")
                curr_pt     = row.get("CurrentPriceTarget") or row.get("currentPriceTarget")
                prior_pt    = row.get("PriorPriceTarget") or row.get("priorPriceTarget")

                # Price target annotation
                if curr_pt and prior_pt and curr_pt != prior_pt:
                    try:
                        direction = "↑" if float(curr_pt) > float(prior_pt) else "↓"
                        pt_note = f"${float(curr_pt):.0f}  {direction} from ${float(prior_pt):.0f}"
                    except (ValueError, TypeError):
                        pt_note = f"${curr_pt}"
                elif curr_pt:
                    try:
                        pt_note = f"${float(curr_pt):.0f}"
                    except (ValueError, TypeError):
                        pt_note = str(curr_pt)
                else:
                    pt_note = ""

                # Action label
                action_lower = str(action).lower()
                if "up" in action_lower:
                    action_label = "↑ upgraded"
                elif "down" in action_lower:
                    action_label = "↓ downgraded"
                else:
                    action_label = "(maintains)"

                rating_changes.append({
                    "date": date.strftime("%b %d"),
                    "firm": firm,
                    "from_grade": from_grade,
                    "to_grade": to_grade,
                    "action_label": action_label,
                    "pt_note": pt_note,
                })
    except Exception:
        pass

    return {
        "symbol": symbol.upper(),
        "consensus": consensus_rows,
        "rating_changes": rating_changes,
        "history_months": history_months,
    }


def format_recommendations(data: Dict[str, Any]) -> str:
    """Format analyst consensus and rating changes for display."""
    symbol = data["symbol"]
    sep = "=" * 60

    lines = [
        f"\n{symbol}  Analyst Consensus",
        sep,
    ]

    # Consensus table
    if data["consensus"]:
        lines.append("")
        lines.append("  CONSENSUS BREAKDOWN")
        lines.append("")
        lines.append(f"  {'Period':<10} {'Strong Buy':>10} {'Buy':>5} {'Hold':>6} {'Sell':>6} {'Strong Sell':>12} {'Total':>7}    Verdict")
        lines.append(f"  {'-'*10} {'-'*10} {'-'*5} {'-'*6} {'-'*6} {'-'*12} {'-'*7}    {'-'*10}")

        period_labels = {"0m": "Now", "-1m": "-1 Month", "-2m": "-2 Months"}
        for row in data["consensus"]:
            label = period_labels.get(row["period"], row["period"])
            lines.append(
                f"  {label:<10} {row['strong_buy']:>10} {row['buy']:>5} {row['hold']:>6}"
                f" {row['sell']:>6} {row['strong_sell']:>12} {row['total']:>7}    → {row['label']}"
            )
    else:
        lines.append("\n  No consensus data available.")

    # Rating changes
    lines.append("")
    lines.append(f"  RECENT RATING CHANGES  (last {data['history_months']} months)")
    lines.append("")

    if data["rating_changes"]:
        for chg in data["rating_changes"]:
            from_g = chg["from_grade"] or "—"
            to_g   = chg["to_grade"]   or "—"
            grade_str = f"{from_g:<18} →  {to_g:<18}"
            pt = f"  {chg['pt_note']}" if chg["pt_note"] else ""
            lines.append(
                f"  {chg['date']:<8} {chg['firm']:<22} {grade_str}{pt}  {chg['action_label']}"
            )
    else:
        lines.append("  No rating changes found in this period.")

    lines.append(f"\n{sep}\n")
    return "\n".join(lines)


# --- Fundamentals Command ---

def _safe_get(df, metric: str) -> Optional[float]:
    """Extract a scalar value from a DataFrame or Series by partial metric name match."""
    if df is None:
        return None
    if isinstance(df, pd.Series):
        for name in df.index:
            if metric.lower() in str(name).lower():
                try:
                    val = df[name]
                    return float(val) if pd.notna(val) else None
                except Exception:
                    return None
        return None
    if df.empty:
        return None
    for name in df.index:
        if metric.lower() in str(name).lower():
            try:
                val = df.loc[name].iloc[0]
                return float(val) if pd.notna(val) else None
            except Exception:
                return None
    return None


def _col_series(df, metric: str, n: int = 4) -> List[float]:
    """Get up to n annual values for a metric from a DataFrame, newest first."""
    if df is None or isinstance(df, pd.Series) or df.empty:
        return []
    for name in df.index:
        if metric.lower() in str(name).lower():
            try:
                return [float(v) for v in df.loc[name].iloc[:n] if pd.notna(v)]
            except Exception:
                return []
    return []


def _cagr(start: float, end: float, years: int) -> Optional[float]:
    if not start or not end or years <= 0 or start <= 0:
        return None
    try:
        return (end / start) ** (1 / years) - 1
    except Exception:
        return None


def _dots(score: float, max_score: float, total: int = 5) -> str:
    filled = round(max(0.0, min(score, max_score)) / max_score * total)
    return "●" * filled + "○" * (total - filled)


def get_fundamentals(symbol: str) -> Dict[str, Any]:
    """Fetch raw fundamental data for scoring."""
    ticker = yf.Ticker(symbol)
    info = ticker.info or {}

    try:
        income   = ticker.income_stmt
        balance  = ticker.balance_sheet
        cashflow = ticker.cashflow
        ttm_inc  = ticker.ttm_income_stmt
        ttm_cf   = ticker.ttm_cashflow
    except Exception as e:
        return {"error": f"Failed to fetch data: {str(e)}"}

    # TTM scalars
    ttm_revenue   = _safe_get(ttm_inc, "Total Revenue")
    ttm_gross     = _safe_get(ttm_inc, "Gross Profit")
    ttm_op_income = _safe_get(ttm_inc, "Operating Income")
    ttm_net       = _safe_get(ttm_inc, "Net Income")
    ttm_fcf       = _safe_get(ttm_cf,  "Free Cash Flow")

    # Annual series (newest → oldest)
    rev_series  = _col_series(income,   "Total Revenue")
    ni_series   = _col_series(income,   "Net Income")
    gp_series   = _col_series(income,   "Gross Profit")
    oi_series   = _col_series(income,   "Operating Income")
    debt_series = _col_series(balance,  "Total Debt")
    eq_series   = _col_series(balance,  "Stockholders Equity")
    ca_series   = _col_series(balance,  "Current Assets")
    cl_series   = _col_series(balance,  "Current Liabilities")
    fcf_series  = _col_series(cashflow, "Free Cash Flow")

    # TTM period label
    ttm_label = "TTM"
    src = ttm_inc if ttm_inc is not None else None
    if src is not None:
        try:
            cols = src.columns if hasattr(src, "columns") else []
            if len(cols):
                ttm_label = f"TTM {cols[0].strftime('%b %Y')}"
        except Exception:
            pass

    # Fiscal year labels from income columns
    fy_labels = []
    if income is not None and not income.empty:
        try:
            fy_labels = [str(c.year) for c in income.columns[:4]]
        except Exception:
            pass

    return {
        "symbol": symbol.upper(),
        "company_name": info.get("longName", ""),
        "ttm_label": ttm_label,
        "fy_labels": fy_labels,
        "ttm_revenue": ttm_revenue,
        "ttm_gross": ttm_gross,
        "ttm_op_income": ttm_op_income,
        "ttm_net": ttm_net,
        "ttm_fcf": ttm_fcf,
        "rev_series": rev_series,
        "ni_series": ni_series,
        "gp_series": gp_series,
        "oi_series": oi_series,
        "fcf_series": fcf_series,
        "total_debt": debt_series[0] if debt_series else None,
        "equity": eq_series[0] if eq_series else None,
        "curr_assets": ca_series[0] if ca_series else None,
        "curr_liab": cl_series[0] if cl_series else None,
        "debt_series": debt_series,
    }


def score_fundamentals(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Compute four-pillar 0-100 health score."""

    def scale(value, threshold, max_pts):
        if value is None:
            return 0.0
        return min(value / threshold, 1.0) * max_pts

    r = raw["ttm_revenue"]

    # ── Pillar 1: Profitability (max 25) ──────────────────────────
    gm = (raw["ttm_gross"]     / r) if r and raw["ttm_gross"]     else None
    nm = (raw["ttm_net"]       / r) if r and raw["ttm_net"]       else None
    om = (raw["ttm_op_income"] / r) if r and raw["ttm_op_income"] else None

    def _avg_margin(num_series, den_series, n=3):
        if len(num_series) >= n and len(den_series) >= n:
            vals = [num_series[i] / den_series[i] for i in range(n) if den_series[i]]
            return sum(vals) / len(vals) if vals else None
        return None

    gm_3yr = _avg_margin(raw["gp_series"], raw["rev_series"])
    margin_delta = (gm - gm_3yr) if gm is not None and gm_3yr is not None else None
    margin_improving = margin_delta is not None and margin_delta > 0

    p1_gm    = scale(gm, 0.50, 8)
    p1_nm    = scale(nm, 0.20, 8)
    p1_om    = scale(om, 0.25, 8)
    p1_trend = 1 if margin_improving else 0
    p1_total = min(round(p1_gm + p1_nm + p1_om + p1_trend), 25)

    # ── Pillar 2: Growth (max 25) ──────────────────────────────────
    rev = raw["rev_series"]
    ni  = raw["ni_series"]

    n_rev  = min(3, len(rev) - 1)
    n_ni   = min(3, len(ni)  - 1)
    rev_cagr = _cagr(rev[n_rev], rev[0], n_rev) if n_rev > 0 else None
    ni_cagr  = _cagr(ni[n_ni],  ni[0],  n_ni)  if n_ni  > 0 else None

    yoy_rev_accel = None
    if len(rev) >= 2 and rev[1]:
        yoy_cur = (rev[0] - rev[1]) / abs(rev[1])
        if len(rev) >= 3 and rev[2]:
            yoy_prev      = (rev[1] - rev[2]) / abs(rev[2])
            yoy_rev_accel = yoy_cur - yoy_prev
        else:
            yoy_rev_accel = yoy_cur

    p2_rev   = scale(rev_cagr, 0.15, 10) if rev_cagr and rev_cagr > 0 else 0
    p2_ni    = scale(ni_cagr,  0.15, 10) if ni_cagr  and ni_cagr  > 0 else 0
    if yoy_rev_accel is not None:
        if yoy_rev_accel > 0.05:
            p2_accel = min(yoy_rev_accel / 0.10 * 5, 5)
        elif yoy_rev_accel < -0.05:
            p2_accel = max(yoy_rev_accel / 0.10 * 2, -2)
        else:
            p2_accel = 0
    else:
        p2_accel = 0
    p2_total = min(max(round(p2_rev + p2_ni + p2_accel), 0), 25)

    # ── Pillar 3: Financial Health (max 25) ────────────────────────
    de_ratio   = None
    curr_ratio = None
    if raw["total_debt"] is not None and raw["equity"]:
        de_ratio = raw["total_debt"] / raw["equity"] if raw["equity"] != 0 else None
    if raw["curr_assets"] is not None and raw["curr_liab"]:
        curr_ratio = raw["curr_assets"] / raw["curr_liab"] if raw["curr_liab"] != 0 else None

    if de_ratio is None:
        p3_de = 0
    elif de_ratio <= 0.5:
        p3_de = 10
    else:
        p3_de = max(0.0, 10 - (de_ratio - 0.5) / 2.5 * 10)

    p3_cr = scale(curr_ratio, 2.0, 10) if curr_ratio is not None else 0

    debt_declining = False
    debt_trend_pts = 0
    ds = raw["debt_series"]
    if ds and len(ds) >= 3:
        if ds[0] < ds[2]:
            debt_declining = True
            debt_trend_pts = 5
        elif ds[0] > ds[2]:
            debt_trend_pts = -2

    p3_total = min(max(round(p3_de + p3_cr + debt_trend_pts), 0), 25)

    # ── Pillar 4: Cash Generation (max 25) ────────────────────────
    fcf = raw["ttm_fcf"]
    fcf_margin   = (fcf / r) if fcf is not None and r else None
    fcf_pos_cnt  = sum(1 for v in raw["fcf_series"][:3] if v and v > 0)
    fcf_quality  = (fcf / raw["ttm_net"]) if fcf is not None and raw["ttm_net"] else None

    p4_margin      = scale(fcf_margin,  0.20, 10) if fcf_margin  and fcf_margin  > 0 else 0
    p4_consistency = (fcf_pos_cnt / 3) * 10
    p4_quality     = scale(fcf_quality, 0.80,  5) if fcf_quality and fcf_quality > 0 else 0
    p4_total       = min(round(p4_margin + p4_consistency + p4_quality), 25)

    total_score = p1_total + p2_total + p3_total + p4_total

    return {
        "symbol":       raw["symbol"],
        "company_name": raw["company_name"],
        "ttm_label":    raw["ttm_label"],
        "fy_labels":    raw["fy_labels"],
        "total_score":  total_score,
        "pillars": {
            "profitability": {
                "score": p1_total,
                "metrics": {
                    "gross_margin":     {"label": "Gross Margin",     "value": gm,            "score": p1_gm,    "max": 8,  "fmt": "pct_ttm"},
                    "net_margin":       {"label": "Net Margin",       "value": nm,            "score": p1_nm,    "max": 8,  "fmt": "pct_ttm"},
                    "operating_margin": {"label": "Operating Margin", "value": om,            "score": p1_om,    "max": 8,  "fmt": "pct_ttm"},
                    "margin_trend":     {"label": "Margin Trend",     "value": margin_delta,  "score": p1_trend, "max": 1,  "fmt": "trend"},
                },
            },
            "growth": {
                "score": p2_total,
                "metrics": {
                    "revenue_cagr": {"label": "Revenue CAGR",    "value": rev_cagr,      "score": p2_rev,   "max": 10, "fmt": "cagr"},
                    "ni_cagr":      {"label": "Net Income CAGR", "value": ni_cagr,       "score": p2_ni,    "max": 10, "fmt": "cagr"},
                    "yoy_accel":    {"label": "YoY Acceleration","value": yoy_rev_accel, "score": p2_accel, "max": 5,  "fmt": "accel"},
                },
            },
            "financial_health": {
                "score": p3_total,
                "metrics": {
                    "debt_equity":   {"label": "Debt-to-Equity", "value": de_ratio,      "score": p3_de,         "max": 10, "fmt": "ratio"},
                    "current_ratio": {"label": "Current Ratio",  "value": curr_ratio,    "score": p3_cr,         "max": 10, "fmt": "ratio"},
                    "debt_trend":    {"label": "Debt Trend",     "value": debt_declining,"score": debt_trend_pts,"max": 5,  "fmt": "debt_trend"},
                },
            },
            "cash_generation": {
                "score": p4_total,
                "metrics": {
                    "fcf_margin":      {"label": "FCF Margin",      "value": fcf_margin,   "score": p4_margin,      "max": 10, "fmt": "pct_ttm"},
                    "fcf_consistency": {"label": "FCF Consistency", "value": fcf_pos_cnt,  "score": p4_consistency, "max": 10, "fmt": "consistency"},
                    "fcf_quality":     {"label": "FCF Quality",     "value": fcf_quality,  "score": p4_quality,     "max": 5,  "fmt": "ratio"},
                },
            },
        },
        "raw": raw,
    }


def format_fundamentals(data: Dict[str, Any], raw_only: bool = False, as_json: bool = False) -> str:
    """Format fundamentals output."""
    if "error" in data:
        return f"Error: {data['error']}"

    if as_json:
        import json
        out = {k: v for k, v in data.items() if k != "raw"}
        return json.dumps(out, indent=2, default=str)

    scored = data  # already scored dict
    symbol  = scored["symbol"]
    name    = scored["company_name"]
    score   = scored["total_score"]
    ttm     = scored["ttm_label"]
    sep     = "=" * 60
    thin    = "─" * 49

    if raw_only:
        raw = scored["raw"]
        lines = [f"\n{symbol}  Raw Fundamentals\n{sep}\n"]
        def _fmt_b(v):
            if v is None: return "N/A"
            return f"${v/1e9:.2f}B"
        def _fmt_p(v):
            if v is None: return "N/A"
            return f"{v*100:.1f}%"
        rev = raw["rev_series"]
        ni  = raw["ni_series"]
        fy  = raw["fy_labels"]
        lines.append(f"  {'Metric':<22} {'TTM':>12} " + "  ".join(f"{l:>12}" for l in fy[:3]))
        lines.append(f"  {'-'*22} {'-'*12} " + "  ".join(f"{'-'*12}" for _ in fy[:3]))
        rows = [
            ("Revenue",       raw["ttm_revenue"],   raw["rev_series"]),
            ("Gross Profit",  raw["ttm_gross"],      raw["gp_series"]),
            ("Op. Income",    raw["ttm_op_income"],  raw["oi_series"]),
            ("Net Income",    raw["ttm_net"],        raw["ni_series"]),
            ("Free Cash Flow",raw["ttm_fcf"],        raw["fcf_series"]),
        ]
        for label, ttm_val, series in rows:
            annual_cols = "  ".join(f"{_fmt_b(v):>12}" for v in series[:3])
            lines.append(f"  {label:<22} {_fmt_b(ttm_val):>12}   {annual_cols}")
        de_str = f"{raw['total_debt']/raw['equity']:.2f}" if raw['total_debt'] and raw['equity'] else 'N/A'
        cr_str = f"{raw['curr_assets']/raw['curr_liab']:.2f}" if raw['curr_assets'] and raw['curr_liab'] else 'N/A'
        lines.append(f"\n  {'Debt-to-Equity':<22} {de_str:>12}")
        lines.append(f"  {'Current Ratio':<22} {cr_str:>12}")
        lines.append(f"\n{sep}\n")
        return "\n".join(lines)

    lines = [
        f"\n{sep}",
        f"  {symbol}  -  {name}",
        f"  Fundamental Health Score: {score}/100",
        sep,
        "",
    ]

    pillar_order = [
        ("profitability",   "PROFITABILITY"),
        ("growth",          "GROWTH"),
        ("financial_health","FINANCIAL HEALTH"),
        ("cash_generation", "CASH GENERATION"),
    ]

    for pillar_key, pillar_name in pillar_order:
        pillar = scored["pillars"][pillar_key]
        pscore = pillar["score"]
        pdots  = _dots(pscore, 25, 5)

        lines.append(f"  {pillar_name:<38} {pscore:>2}/25   {pdots}")
        lines.append(f"  {thin}")

        for m in pillar["metrics"].values():
            label  = m["label"]
            value  = m["value"]
            fmt    = m["fmt"]
            mscore = m["score"]
            mmax   = m["max"]

            if value is None:
                val_str = "N/A"
            elif fmt == "pct_ttm":
                val_str = f"{value*100:.1f}%   ({ttm})"
            elif fmt == "cagr":
                val_str = f"3yr  {value*100:+.1f}%"
            elif fmt == "ratio":
                val_str = f"{value:.2f}"
            elif fmt == "trend":
                direction = "Improving" if value > 0 else "Declining"
                val_str   = f"{direction}  ({value*100:+.1f}% vs 3yr avg)"
            elif fmt == "accel":
                if abs(value) <= 0.02:
                    direction = "Stable"
                elif value > 0:
                    direction = "Accelerating"
                else:
                    direction = "Decelerating"
                val_str = f"Revenue {direction} ({value*100:+.1f}%)"
            elif fmt == "debt_trend":
                val_str = "Declining 3 years" if value else "Increasing / Flat"
            elif fmt == "consistency":
                val_str = f"Positive {int(value)}/3 years"
            else:
                val_str = str(value)

            mdots = _dots(max(mscore, 0), mmax, 5)
            lines.append(f"  {label:<20} {val_str:<34} {mdots}")

        lines.append("")

    fy = scored["fy_labels"]
    fy_range = f"Annual FY{fy[-1]}–FY{fy[0]}" if fy else "Annual"
    lines.append(sep)
    lines.append(f"  Data: {fy_range} + {ttm}")
    lines.append(f"{sep}\n")

    return "\n".join(lines)


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
    chart_parser.add_argument("--interval", "-i", default="1d", help="Interval: 1m,5m,15m,1h,1d,1wk,1mo (default: 1d)")
    chart_parser.add_argument("--type", "-t", choices=["candlestick", "line"], default="candlestick", help="Chart type")
    chart_parser.add_argument("--output", "-o", help="Output file path")
    chart_parser.add_argument("--width", type=int, default=1200, help="Width in pixels (default: 1200)")
    chart_parser.add_argument("--height", type=int, default=800, help="Height in pixels (default: 800)")
    chart_parser.add_argument("--ma", nargs="+", type=int, default=[], help="Moving average periods to overlay (e.g. --ma 20 50 200)")
    chart_parser.add_argument("--background", "-b", choices=["transparent", "white", "black"], default="white", help="Background color (default: white)")

    # fundamentals command
    fund_parser = subparsers.add_parser("fundamentals", help="Four-pillar fundamental health score (0-100)")
    fund_parser.add_argument("symbol", help="Stock ticker symbol (e.g., AAPL)")
    fund_parser.add_argument("--raw",  action="store_true", help="Print underlying numbers without scoring")
    fund_parser.add_argument("--json", action="store_true", dest="as_json", help="Output as JSON for agent/LLM use")

    # recommendations command
    rec_parser = subparsers.add_parser("recommendations", help="Analyst consensus and recent rating changes")
    rec_parser.add_argument("symbol", help="Stock ticker symbol (e.g., AAPL)")
    rec_parser.add_argument("--history", "-H", type=int, default=3, help="Months of rating history to show (default: 3)")

    # news command
    news_parser = subparsers.add_parser("news", help="Get latest news for a ticker or search query")
    news_parser.add_argument("query", help="Ticker symbol or search query (e.g., AAPL or 'oil prices')")
    news_parser.add_argument("--count", "-n", type=int, default=5, help="Number of articles (default: 5)")
    news_parser.add_argument("--summary", "-s", action="store_true", help="Show full summary paragraph")

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

    elif args.command == "fundamentals":
        raw  = get_fundamentals(args.symbol)
        data = score_fundamentals(raw) if "error" not in raw else raw
        print(format_fundamentals(data, raw_only=args.raw, as_json=args.as_json))

    elif args.command == "recommendations":
        data = get_recommendations(args.symbol, history_months=args.history)
        print(format_recommendations(data))

    elif args.command == "news":
        data = get_news(args.query, count=args.count)
        print(format_news(data, full_summary=args.summary))

    elif args.command == "chart":
        result = generate_chart(
            args.symbol,
            period=args.period,
            interval=args.interval,
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
