"""Run a backtest with a choice of instrument, strategy, and starting capital.

Examples:
    .venv/bin/python run_backtest.py                                          # MES + EMA, $1k
    .venv/bin/python run_backtest.py --strategy breakout --capital 1000       # MES + breakout, $1k
    .venv/bin/python run_backtest.py --instrument ES --capital 1000000        # full ES, $1m
    .venv/bin/python run_backtest.py --instrument NQ --strategy breakout --leverage 50
"""

from __future__ import annotations

import argparse
import datetime as dt
from decimal import Decimal

from trading_floor.backtest import run_backtest
from trading_floor.data import generate_bars
from trading_floor.data import make_bar_type
from trading_floor.instruments import CME
from trading_floor.instruments import es_future
from trading_floor.instruments import mes_future
from trading_floor.instruments import mnq_future
from trading_floor.instruments import nq_future
from trading_floor.strategies import BreakoutConfig
from trading_floor.strategies import BreakoutStrategy
from trading_floor.strategies import EmaCrossConfig
from trading_floor.strategies import EmaCrossStrategy

# Each instrument: (builder function, a realistic approximate price, tick size).
INSTRUMENTS = {
    "ES": (es_future, 5900.0),
    "NQ": (nq_future, 20500.0),
    "MES": (mes_future, 5900.0),
    "MNQ": (mnq_future, 20500.0),
}


def build_strategy(name: str, instrument_id, bar_type, trade_size: Decimal):
    """Create a strategy instance by name."""

    if name == "ema":
        return EmaCrossStrategy(
            EmaCrossConfig(
                instrument_id=instrument_id,
                bar_type=bar_type,
                trade_size=trade_size,
                fast_period=12,
                slow_period=26,
            )
        )
    if name == "breakout":
        return BreakoutStrategy(
            BreakoutConfig(
                instrument_id=instrument_id,
                bar_type=bar_type,
                trade_size=trade_size,
                lookback=20,
            )
        )
    raise ValueError(f"Unknown strategy: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest a futures strategy.")
    parser.add_argument("--instrument", default="MES", choices=list(INSTRUMENTS))
    parser.add_argument("--strategy", default="ema", choices=["ema", "breakout"])
    parser.add_argument("--capital", type=float, default=1000.0, help="Starting USD balance")
    parser.add_argument("--leverage", type=int, default=50, help="Buying-power multiplier")
    parser.add_argument("--periods", type=int, default=4000, help="Number of bars")
    args = parser.parse_args()

    builder, initial_price = INSTRUMENTS[args.instrument]
    instrument = builder()

    bar_type = make_bar_type(instrument.id, step=5)
    bars = generate_bars(
        bar_type=bar_type,
        start=dt.datetime(2026, 9, 1, tzinfo=dt.timezone.utc),
        periods=args.periods,
        initial_price=initial_price,
        interval="5min",
    )
    print(f"{args.instrument} | {args.strategy} | capital ${args.capital:,.0f} | "
          f"leverage {args.leverage} | {len(bars)} bars")

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
    print(f"Fills:          {len(fills)}")
    print(f"Round trips:    {len(positions)}")
    print(f"Final balance:  ${final_balance:,.2f}")
    print(f"Net PnL:        ${net_pnl:,.2f}")


if __name__ == "__main__":
    main()
