"""Run a backtest on REAL market data downloaded from Databento.

Requires a Databento API key (see realdata.py).

Examples:
    export DATABENTO_API_KEY='db-xxxx'

    .venv/bin/python run_real_backtest.py --symbol MESZ6 --start 2026-09-01 --end 2026-10-01
    .venv/bin/python run_real_backtest.py --symbol ESZ6 --strategy breakout --capital 1000000
"""

from __future__ import annotations

import argparse
from decimal import Decimal

from trading_floor.backtest import run_backtest
from trading_floor.instruments import CME
from trading_floor.instruments import es_future
from trading_floor.instruments import mes_future
from trading_floor.instruments import mnq_future
from trading_floor.instruments import nq_future
from trading_floor.realdata import download_bars
from trading_floor.realdata import load_bars
from trading_floor.strategies import build_strategy

# Map a concrete contract symbol (e.g. "MESZ6") to the matching instrument builder.
_BUILDERS = {
    "MES": mes_future,
    "MNQ": mnq_future,
    "ES": es_future,
    "NQ": nq_future,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest on real Databento data.")
    parser.add_argument("--symbol", default="MESZ6", help="e.g. MESZ6, ESZ6, NQZ6")
    parser.add_argument("--start", default="2026-09-01", help="inclusive start date")
    parser.add_argument("--end", default="2026-10-01", help="exclusive end date")
    parser.add_argument("--schema", default="ohlcv-1m", help="ohlcv-1m, ohlcv-1h, ohlcv-1d")
    parser.add_argument("--strategy", default="ema", choices=["ema", "breakout"])
    parser.add_argument("--capital", type=float, default=1000.0)
    parser.add_argument("--leverage", type=int, default=50)
    args = parser.parse_args()

    prefix = args.symbol[:3].upper()
    builder = _BUILDERS.get(prefix)
    if builder is None:
        raise SystemExit(f"Unknown symbol prefix: {prefix!r} (expected MES/MNQ/ES/NQ)")

    instrument = builder(symbol=args.symbol)
    print(f"{args.symbol} | {args.strategy} | capital ${args.capital:,.0f}")

    path = download_bars(args.symbol, start=args.start, end=args.end, schema=args.schema)
    bars = load_bars(path, instrument.id)

    if not bars:
        raise SystemExit(f"No bars loaded for {args.symbol} in that date range.")

    bar_type = bars[0].bar_type  # take the bar type directly from the real data

    strategy = build_strategy(args.strategy, instrument.id, bar_type, Decimal("1"))

    account, fills, positions = run_backtest(
        strategy=strategy,
        instrument=instrument,
        bars=bars,
        venue=CME,
        starting_cash=Decimal(str(int(args.capital))),
        default_leverage=Decimal(args.leverage),
    )

    final_balance = float(account["total"].iloc[-1])
    net_pnl = final_balance - args.capital

    print("=== RESULT ===")
    print(f"Bars:          {len(bars)}")
    print(f"Fills:         {len(fills)}")
    print(f"Round trips:   {len(positions)}")
    print(f"Final balance: ${final_balance:,.2f}")
    print(f"Net PnL:       ${net_pnl:,.2f}")


if __name__ == "__main__":
    main()
