"""Synthetic market-data generation.

Real ES/NQ historical data requires a paid provider (Databento, Polygon.io,
IQFeed, etc.) and API keys. To keep the first milestone runnable with *zero*
external dependencies, we generate a realistic-looking random-walk price series.

This is NOT a tradable edge — it's a way to learn the NautilusTrader data model
and backtest engine before plugging in real data.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.model.data import Bar
from nautilus_trader.model.data import BarSpecification
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import BarAggregation
from nautilus_trader.model.enums import PriceType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity


def make_bar_type(instrument_id: InstrumentId, step: int = 5) -> BarType:
    """Build a `step`-minute, last-price bar type for the instrument."""

    spec = BarSpecification(step=step, aggregation=BarAggregation.MINUTE, price_type=PriceType.LAST)
    return BarType(instrument_id, spec)


def _round_tick(price: float, tick_size: float) -> float:
    """Round a raw price to the nearest tick increment."""

    return round(round(price / tick_size) * tick_size, 2)


def generate_bars(
    bar_type: BarType,
    start: dt.datetime,
    periods: int,
    initial_price: float,
    tick_size: float = 0.25,
    interval: str = "5min",
    seed: int = 42,
) -> list[Bar]:
    """Generate a synthetic random-walk series of OHLC bars.

    Returns a list of ``Bar`` objects, one per interval, ready to feed into a
    backtest engine via ``engine.add_data(...)``.
    """

    rng = np.random.default_rng(seed)

    # Geometric random walk for the close prices (log-returns).
    log_returns = rng.normal(0.0, 0.0008, periods)
    closes = initial_price * np.exp(np.cumsum(log_returns))

    # Timestamps, one per interval, in UTC.
    timestamps = pd.date_range(start, periods=periods, freq=interval, tz="UTC")

    bars: list[Bar] = []
    prev_close = closes[0]

    for i in range(periods):
        open_ = prev_close if i > 0 else closes[0]
        close = closes[i]

        # Build a valid OHLC bar: high >= max(open, close), low <= min(open, close).
        high = max(open_, close) + abs(rng.normal(0.0, 0.05)) + tick_size
        low = min(open_, close) - abs(rng.normal(0.0, 0.05)) - tick_size

        open_ = _round_tick(open_, tick_size)
        close = _round_tick(close, tick_size)
        high = max(_round_tick(high, tick_size), open_, close)
        low = min(_round_tick(low, tick_size), open_, close)

        ts = dt_to_unix_nanos(timestamps[i])
        volume = Quantity.from_int(int(rng.integers(500, 5_000)))

        bars.append(
            Bar(
                bar_type=bar_type,
                open=Price.from_str(f"{open_:.2f}"),
                high=Price.from_str(f"{high:.2f}"),
                low=Price.from_str(f"{low:.2f}"),
                close=Price.from_str(f"{close:.2f}"),
                volume=volume,
                ts_event=ts,
                ts_init=ts,
            )
        )

        prev_close = close

    return bars
