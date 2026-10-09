"""Futures contract definitions for the CME index products we target.

This module builds ``FuturesContract`` objects for:

- ES — the E-mini S&P 500 futures (the "S&P 500" the user trades).
- NQ — the E-mini Nasdaq-100 futures (the "Nasdaq" the user trades).

These are real contract specifications:

- ES: tick size 0.25, multiplier 50 (each point = $50), USD-denominated.
- NQ: tick size 0.25, multiplier 20 (each point = $20), USD-denominated.

Both have a price precision of 2 decimal places.

The symbol names below are illustrative (e.g. ``ESZ6`` mimics the December 2026
contract). In production these would come from a real data source.
"""

from __future__ import annotations

import datetime as dt

from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.enums import AssetClass
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import Symbol
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.instruments import FuturesContract
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity

# The Chicago Mercantile Exchange, where ES and NQ futures trade.
CME = Venue("CME")


def _build_futures(
    symbol: str,
    underlying: str,
    multiplier: int,
    activation: dt.datetime,
    expiration: dt.datetime,
) -> FuturesContract:
    """Build a CME index-futures contract with common ES/NQ properties."""

    return FuturesContract(
        instrument_id=InstrumentId(Symbol(symbol), CME),
        raw_symbol=Symbol(symbol),
        asset_class=AssetClass.INDEX,
        currency=USD,
        price_precision=2,
        price_increment=Price.from_str("0.25"),  # 1 tick = 0.25 index points
        multiplier=Quantity.from_int(multiplier),
        lot_size=Quantity.from_int(1),
        underlying=underlying,
        activation_ns=dt_to_unix_nanos(activation),
        expiration_ns=dt_to_unix_nanos(expiration),
        ts_event=0,
        ts_init=0,
    )


def es_future(
    symbol: str = "ESZ6",
    activation: dt.datetime | None = None,
    expiration: dt.datetime | None = None,
) -> FuturesContract:
    """Return an E-mini S&P 500 futures contract (multiplier 50)."""

    activation = activation or dt.datetime(2026, 9, 1, tzinfo=dt.timezone.utc)
    expiration = expiration or dt.datetime(2026, 12, 18, 21, 30, tzinfo=dt.timezone.utc)
    return _build_futures(symbol, "ES", multiplier=50, activation=activation, expiration=expiration)


def nq_future(
    symbol: str = "NQZ6",
    activation: dt.datetime | None = None,
    expiration: dt.datetime | None = None,
) -> FuturesContract:
    """Return an E-mini Nasdaq-100 futures contract (multiplier 20)."""

    activation = activation or dt.datetime(2026, 9, 1, tzinfo=dt.timezone.utc)
    expiration = expiration or dt.datetime(2026, 12, 18, 21, 30, tzinfo=dt.timezone.utc)
    return _build_futures(symbol, "NQ", multiplier=20, activation=activation, expiration=expiration)


def mes_future(
    symbol: str = "MESZ6",
    activation: dt.datetime | None = None,
    expiration: dt.datetime | None = None,
) -> FuturesContract:
    """Return a *Micro* E-mini S&P 500 futures contract (multiplier 5).

    Micros are 1/10th the size of the full contract, which is what a small
    account (~$1k) can realistically trade.
    """

    activation = activation or dt.datetime(2026, 9, 1, tzinfo=dt.timezone.utc)
    expiration = expiration or dt.datetime(2026, 12, 18, 21, 30, tzinfo=dt.timezone.utc)
    return _build_futures(symbol, "MES", multiplier=5, activation=activation, expiration=expiration)


def mnq_future(
    symbol: str = "MNQZ6",
    activation: dt.datetime | None = None,
    expiration: dt.datetime | None = None,
) -> FuturesContract:
    """Return a *Micro* E-mini Nasdaq-100 futures contract (multiplier 2)."""

    activation = activation or dt.datetime(2026, 9, 1, tzinfo=dt.timezone.utc)
    expiration = expiration or dt.datetime(2026, 12, 18, 21, 30, tzinfo=dt.timezone.utc)
    return _build_futures(symbol, "MNQ", multiplier=2, activation=activation, expiration=expiration)
