# CLAUDE.md — stocks.py

## Project Overview

`stocks.py` is a single-file CLI tool for stock market data, backed by Yahoo Finance via the `yfinance` library. It is also packaged as an **agent skill** — a self-contained, documented tool that AI agents can call directly as a subprocess.

The project has two distinct consumers:
- **Human users** running `stocks.py <command>` directly from the terminal
- **AI agents** reading `SKILL.md` to understand available commands, then running them as subprocesses and parsing stdout

---

## Repository Layout

```
stocks.py/
├── scripts/
│   └── stocks.py          # The entire CLI — single file, all commands
├── SKILL.md             # Agent-facing reference (commands, options, output semantics)
├── README.md            # Human-facing docs (installation, usage, examples)
└── CLAUDE.md            # This file
```

---

## The CLI Tool (`scripts/stocks.py`)

### Execution Model

Uses the `uv run --script` shebang pattern (PEP 723) with inline dependency declarations:

```python
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
```

Run directly: `uv run --script scripts/stocks.py <command>` or, if installed in PATH, `stocks.py <command>`.

### Code Structure

Each command follows the same three-part pattern:

1. **`get_*()`** — fetches and normalizes data from yfinance, returns a plain `Dict[str, Any]`
2. **`format_*()`** — takes the dict, returns a formatted string for stdout
3. **Subparser + dispatch** — registered in `main()`, calls get → format → print

The data dict always includes an `"error"` key on failure instead of raising exceptions. Formatters check for this first.

### Commands

| Command | Get function | Format function | Key data source |
|---------|-------------|-----------------|-----------------|
| `quote` | `get_quote()` | `format_quote()` | `ticker.info`, `ticker.history()` |
| `search` | `search_ticker()` | `format_search()` | Yahoo Finance search API |
| `history` | `get_history()` | `format_history()` | `ticker.history()` |
| `chart` | `generate_chart()` | — (returns filepath) | `ticker.history()` + matplotlib |
| `news` | `get_news()` | `format_news()` | `yf.Search(query).news` |
| `recommendations` | `get_recommendations()` | `format_recommendations()` | `ticker.recommendations_summary`, `ticker.upgrades_downgrades` |
| `fundamentals` | `get_fundamentals()` | `format_fundamentals()` | `ticker.income_stmt`, `ticker.balance_sheet`, `ticker.cashflow`, TTM variants |

### Fundamentals Pipeline

`fundamentals` is the most complex command — it has a three-stage pipeline:

```
get_fundamentals(symbol)      →  raw dict (all financial data)
score_fundamentals(raw)       →  scored dict (pillars + total score + raw embedded)
format_fundamentals(scored)   →  stdout string (or JSON / raw table via flags)
```

The `main()` dispatch calls all three stages explicitly so scoring logic stays separate from formatting.

### Helper Functions (fundamentals)

- `_safe_get(df, metric)` — extracts a scalar from a DataFrame or Series by partial metric name match (case-insensitive). Handles both Series (TTM) and DataFrame (annual) shapes.
- `_col_series(df, metric, n=4)` — extracts up to `n` annual values for a metric, newest first (column index order matches yfinance column ordering).
- `_cagr(start, end, years)` — compound annual growth rate, returns `None` on invalid inputs.
- `_dots(score, max_score, total=5)` — returns a `●●●●○` dot meter string.

### yfinance Data Shape Notes

- `ticker.income_stmt` / `ticker.balance_sheet` / `ticker.cashflow` — DataFrame where **columns are dates (newest first)** and **rows are metric names**. Index strings can vary slightly; use partial lowercase matching.
- `ticker.ttm_income_stmt` / `ticker.ttm_cashflow` — may be a Series or single-column DataFrame depending on yfinance version. `_safe_get()` handles both.
- `ticker.upgrades_downgrades` — DataFrame indexed by `GradeDate` (timezone-naive `pd.Timestamp`). Use `pd.Timestamp.now()` (no tz) for cutoff comparisons.
- `ticker.recommendations_summary` — DataFrame with `period` column (`"0m"`, `"-1m"`, `"-2m"`) and columns `strongBuy`, `buy`, `hold`, `sell`, `strongSell`.
- `yf.Search(query, news_count=n).news` — returns a list of dicts with keys: `title`, `publisher`, `link`, `providerPublishTime` (Unix timestamp int), `type`, `relatedTickers`. No `summary` field in this path.

---

## The Skill (`SKILL.md`)

`SKILL.md` is the agent-facing contract. It follows the skill frontmatter format:

```yaml
---
name: stocks
description: <one-line trigger description for the agent>
compatibility: <runtime requirement>
---
```

The `description` field is what an agent uses to decide when to invoke this skill. Keep it comprehensive but accurate — it should list all major use cases so the agent picks this skill for the right queries.

### Skill vs README

| | `SKILL.md` | `README.md` |
|--|-----------|-------------|
| Audience | AI agents | Human developers/users |
| Tone | Precise, structured, scannable | Friendly, instructional |
| Focus | Command syntax, return values, option semantics | Installation, features, examples |
| Workflows | Agent pipelines (JSON output, screening loops) | Human workflows (charting, research) |

When adding a new command, update **both** files. SKILL.md should include the exact output fields the agent will need to parse or pass to an LLM.

---

## Adding a New Command

1. Add a `get_<name>()` function that returns `Dict[str, Any]` with `"error"` on failure
2. Add a `format_<name>()` function that checks for `"error"` first, then formats stdout
3. Register a subparser in `main()` with `subparsers.add_parser(...)`
4. Add a dispatch case in `main()` calling get → format → print
5. Update the docstring at the top of the file
6. Update `SKILL.md` — command section, options table, relevant workflow examples
7. Update `README.md` — Features list, Commands table, Usage section, Command Options table

---

## Scoring Model (`fundamentals`)

Four pillars, each 0–25, summed to 0–100:

### Pillar 1 — Profitability
| Metric | Max pts | Full-score threshold |
|--------|---------|----------------------|
| Gross Margin (TTM) | 8 | ≥ 50% |
| Net Margin (TTM) | 8 | ≥ 20% |
| Operating Margin (TTM) | 8 | ≥ 25% |
| Margin Trend (TTM vs 3yr avg gross margin) | 1 | Improving |

### Pillar 2 — Growth
| Metric | Max pts | Full-score threshold |
|--------|---------|----------------------|
| Revenue CAGR (3yr) | 10 | ≥ 15% |
| Net Income CAGR (3yr) | 10 | ≥ 15% |
| YoY Revenue Acceleration | ±5 / -2 | +5% accel = full bonus |

### Pillar 3 — Financial Health
| Metric | Max pts | Full-score threshold |
|--------|---------|----------------------|
| Debt-to-Equity | 10 | ≤ 0.5 (linear decay to 3.0) |
| Current Ratio | 10 | ≥ 2.0 |
| Debt Trend (3yr) | +5 / -2 | Declining = +5, Increasing = -2 |

### Pillar 4 — Cash Generation
| Metric | Max pts | Full-score threshold |
|--------|---------|----------------------|
| FCF Margin (TTM) | 10 | ≥ 20% |
| FCF Consistency (3yr) | 10 | All 3 years positive |
| FCF Quality (FCF/NI) | 5 | ≥ 0.8 |

All metrics scale linearly from 0 to their threshold. Negative values (losses, negative FCF) score 0, not negative. Pillar totals are capped at 25.

---

## Agent Use Case

These three commands form the core analysis stack for an agent:

```bash
stocks.py fundamentals <TICKER> --json   # Objective business quality signal
stocks.py recommendations <TICKER>       # Forward-looking analyst sentiment
stocks.py news <TICKER|TOPIC>            # Real-time context
```

The `--json` flag on `fundamentals` outputs a structured dict with `total_score`, all four pillar scores, and per-metric values — suitable for passing directly to an LLM prompt. The score (0–100) also enables ranking: run across a list of tickers and sort by `total_score` to screen candidates.
