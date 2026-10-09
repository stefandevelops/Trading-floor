# Trading Floor

An educational project to build a *"trading floor"* of automated trading agents for
**E-mini S&P 500 (ES)** and **E-mini Nasdaq-100 (NQ)** futures, built on
**[NautilusTrader](https://nautilustrader.io/)**.

> ⚠️ **Learning project — not financial advice, and not a live money-making bot.**
> This is a step-by-step curriculum project to learn Python, automated trading
> systems, and backtesting. The synthetic data has no edge, and the strategy is a
> textbook example.

---

## Why NautilusTrader?

NautilusTrader is an open-source, production-grade, event-driven trading engine. It
gives you one codebase for **research, backtesting, and (eventually) live trading**,
with a proper domain model (instruments, orders, fills, positions, accounts) and
support for futures. That is exactly the foundation a multi-agent "trading floor"
would sit on.

## What works so far (Milestone 1)

A complete, runnable backtest pipeline with zero external data or API keys:

1. **Instruments** — real ES/NQ futures contract specs (`instruments.py`).
2. **Data** — a synthetic random-walk bar generator (`data.py`).
3. **Strategy** — a dual-EMA crossover (`strategies.py`).
4. **Engine** — full backtest wiring (`backtest.py`).
5. **Run** — `run_backtest.py` ties it together and prints results.

## Setup

Requires Python 3.12–3.14 (tested on 3.14).

```bash
cd trading-floor
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run

```bash
.venv/bin/python run_backtest.py
```

You'll see the engine's full performance report (PnL, Sharpe, profit factor,
win/loss stats) followed by a short headline summary.

## Project structure

```
trading-floor/
├── trading_floor/          # the Python package
│   ├── instruments.py      # ES / NQ futures contracts
│   ├── data.py             # synthetic bar generation
│   ├── strategies.py       # EMA crossover strategy
│   └── backtest.py         # engine setup + runner helper
├── run_backtest.py         # entry point
├── requirements.txt
└── README.md
```

## Key concepts you'll meet

| Concept | Where |
|---|---|
| Instrument / futures contract | `instruments.py` |
| Bars & market data | `data.py` |
| Indicators (EMA) | `strategies.py` |
| Strategy lifecycle (`on_start`, `on_bar`, `on_stop`) | `strategies.py` |
| Orders, fills, positions | `strategies.py` + `backtest.py` |
| Backtest engine & venue | `backtest.py` |

## Important caveats

- **Synthetic data ≠ real edge.** The random walk is only for learning the engine.
- **No fees/fill latency configured yet** (defaults applied). Realism comes later.
- **Prop firms & automation:** most futures prop firms forbid fully-autonomous
  trading on funded accounts in their terms of service. Read yours before ever
  connecting live orders. The intended path here is *research-first*, with
  human-in-the-loop confirmation if you ever go live.

## Roadmap (next milestones)

- [ ] **M2 — Real data**: load real ES/NQ historical bars from a provider
      (Databento, Polygon.io, etc.) into a Parquet data catalog.
- [ ] **M3 — More instruments & strategies**: run ES *and* NQ, parameterize the
      strategy, add a risk module (position limits, daily loss cap).
- [ ] **M4 — The "floor"**: split responsibilities into separate agents (signal
      agent, risk agent, journaling agent) sharing one engine.
- [ ] **M5 — Paper/live**: connect an execution adapter (e.g. Interactive Brokers,
      Tradovate, Rithmic) with a human-approval gate.
