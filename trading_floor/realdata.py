"""Real market data via Databento.

Downloads CME futures data as DBN files and decodes them into NautilusTrader
``Bar`` objects that feed the exact same backtest engine as the synthetic data.

Requires a Databento API key exposed as the ``DATABENTO_API_KEY`` environment
variable. Sign up at https://databento.com (new users get $125 in credits).
"""

from __future__ import annotations

import os
from pathlib import Path

import databento as db

from nautilus_trader.adapters.databento import DatabentoDataLoader
from nautilus_trader.model.data import Bar
from nautilus_trader.model.identifiers import InstrumentId

# CME Globex MDP 3.0 — the CME/CBOT/NYMEX/COMEX futures dataset.
DATASET = "GLBX.MDP3"


def download_bars(
    symbol: str,
    start: str,
    end: str,
    schema: str = "ohlcv-1m",
    out_dir: str = "data",
) -> Path:
    """Download historical bars for ``symbol`` and save as a DBN file.

    Examples of ``symbol``: ``"MESZ6"`` (Dec 2026 micro S&P 500), ``"ESZ6"``.
    ``schema``: ``"ohlcv-1m"`` (1-min bars), ``"ohlcv-1h"``, ``"ohlcv-1d"``.
    """

    key = os.environ.get("DATABENTO_API_KEY")
    if not key:
        raise SystemExit(
            "DATABENTO_API_KEY is not set.\n"
            "1. Sign up at https://databento.com\n"
            "2. Copy your API key from the portal\n"
            "3. Run:  export DATABENTO_API_KEY='your-key'\n"
            "   (or 'set DATABENTO_API_KEY=your-key' on Windows)"
        )

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{symbol}_{schema}.dbn.zst"

    client = db.Historical()  # reads DATABENTO_API_KEY
    client.timeseries.get_range(
        dataset=DATASET,
        symbols=symbol,
        schema=schema,
        start=start,
        end=end,
        path=str(path),
    )

    print(f"Downloaded {symbol} {schema} -> {path}")
    return path


def load_bars(path: Path | str, instrument_id: InstrumentId) -> list[Bar]:
    """Decode a DBN bar file into NautilusTrader ``Bar`` objects.

    ``instrument_id`` is applied to every bar (e.g. ``MESZ6.CME``) so the bars
    line up with the instrument you built in ``instruments.py``.
    """

    loader = DatabentoDataLoader()
    data = loader.from_dbn_file(
        str(path),
        instrument_id=instrument_id,
        price_precision=2,  # ES/NQ/MES/MNQ all use 2 decimal places (0.25 tick)
    )
    bars = [d for d in data if isinstance(d, Bar)]
    print(f"Loaded {len(bars)} bars from {path}")
    return bars
