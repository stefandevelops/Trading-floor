"""Backtest engine wiring.

Ties together the pieces into a runnable NautilusTrader backtest:

1. Create the engine.
2. Add a simulated exchange (venue) with a starting balance.
3. Add the instrument.
4. Add the data (bars).
5. Add the strategy.
6. Run.
7. Pull out the resulting reports.
"""

from __future__ import annotations

from decimal import Decimal

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.engine import BacktestEngineConfig
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.data import Bar
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import OmsType
from nautilus_trader.model.identifiers import TraderId
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.instruments import FuturesContract
from nautilus_trader.model.objects import Money
from nautilus_trader.trading.strategy import Strategy


def run_backtest(
    strategy: Strategy,
    instrument: FuturesContract,
    bars: list[Bar],
    venue: Venue,
    starting_cash: Decimal = Decimal("1000000"),
    default_leverage: Decimal = Decimal("1"),
) -> tuple:
    """Run a single-instrument, single-strategy backtest.

    ``default_leverage`` = account buying power multiplier. With 1 (default) the
    account must post the full contract notional as margin; a higher value lets
    a small account control a larger position (like a leverage prop account).

    Returns ``(account_report, fills_report, positions_report)`` as DataFrames.
    """

    config = BacktestEngineConfig(
        trader_id=TraderId("BACKTESTER-001"),
    )

    engine = BacktestEngine(config)

    engine.add_venue(
        venue=venue,
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        starting_balances=[Money(starting_cash, USD)],
        base_currency=USD,
        default_leverage=default_leverage,
    )

    engine.add_instrument(instrument)
    engine.add_data(bars)
    engine.add_strategy(strategy)

    engine.run()

    account = engine.trader.generate_account_report(venue)
    fills = engine.trader.generate_order_fills_report()
    positions = engine.trader.generate_positions_report()

    engine.dispose()

    return account, fills, positions
