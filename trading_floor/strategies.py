"""Trading strategies.

Your first strategy: a dual exponential-moving-average (EMA) crossover.

When the fast EMA crosses above the slow EMA we go long; when it crosses below
we go short. It flips the position on every cross. This is a classic teaching
strategy — it has *no* real edge, but it exercises the full NautilusTrader
lifecycle (indicators, signals, orders, fills, positions) in a clean, small file.
"""

from __future__ import annotations

from collections import deque
from decimal import Decimal

from nautilus_trader.config import PositiveInt
from nautilus_trader.config import StrategyConfig
from nautilus_trader.indicators import ExponentialMovingAverage
from nautilus_trader.model.data import Bar
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.trading.strategy import Strategy


def build_strategy(
    name: str,
    instrument_id: InstrumentId,
    bar_type: BarType,
    trade_size: Decimal,
) -> Strategy:
    """Create a strategy instance by name (used by both the synthetic and real-data runners)."""

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


class EmaCrossConfig(StrategyConfig, frozen=True):
    """Configuration for ``EmaCrossStrategy``."""

    instrument_id: InstrumentId
    bar_type: BarType
    trade_size: Decimal
    fast_period: PositiveInt = 12
    slow_period: PositiveInt = 26


class EmaCrossStrategy(Strategy):
    """A dual-EMA crossover strategy that is always in the market."""

    def __init__(self, config: EmaCrossConfig) -> None:
        if config.fast_period >= config.slow_period:
            raise ValueError("fast_period must be less than slow_period")
        super().__init__(config)

        self.instrument: Instrument | None = None
        self.fast_ema = ExponentialMovingAverage(config.fast_period)
        self.slow_ema = ExponentialMovingAverage(config.slow_period)

    def on_start(self) -> None:
        self.instrument = self.cache.instrument(self.config.instrument_id)
        if self.instrument is None:
            self.log.error(f"Instrument not found: {self.config.instrument_id}")
            self.stop()
            return

        # Wire the EMAs to be updated automatically whenever a bar arrives.
        self.register_indicator_for_bars(self.config.bar_type, self.fast_ema)
        self.register_indicator_for_bars(self.config.bar_type, self.slow_ema)

        # Tell the engine we want this bar stream (data is pre-loaded in backtest).
        self.subscribe_bars(self.config.bar_type)

    def on_bar(self, bar: Bar) -> None:
        # Wait until both EMAs have enough data to produce a value.
        if not self.indicators_initialized():
            return

        if self.fast_ema.value > self.slow_ema.value:
            if self.portfolio.is_flat(self.config.instrument_id):
                self._submit(OrderSide.BUY)
            elif self.portfolio.is_net_short(self.config.instrument_id):
                # Fast crossed back above slow while short -> flip to long.
                self.close_all_positions(self.config.instrument_id)
                self._submit(OrderSide.BUY)
        elif self.fast_ema.value < self.slow_ema.value:
            if self.portfolio.is_flat(self.config.instrument_id):
                self._submit(OrderSide.SELL)
            elif self.portfolio.is_net_long(self.config.instrument_id):
                # Fast crossed below slow while long -> flip to short.
                self.close_all_positions(self.config.instrument_id)
                self._submit(OrderSide.SELL)

    def _submit(self, side: OrderSide) -> None:
        order = self.order_factory.market(
            instrument_id=self.config.instrument_id,
            order_side=side,
            quantity=self.instrument.make_qty(self.config.trade_size),
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)

    def on_stop(self) -> None:
        self.cancel_all_orders(self.config.instrument_id)
        self.close_all_positions(self.config.instrument_id)

    def on_reset(self) -> None:
        self.fast_ema.reset()
        self.slow_ema.reset()


class BreakoutConfig(StrategyConfig, frozen=True):
    """Configuration for ``BreakoutStrategy``."""

    instrument_id: InstrumentId
    bar_type: BarType
    trade_size: Decimal
    lookback: PositiveInt = 20


class BreakoutStrategy(Strategy):
    """A Donchian-channel breakout strategy.

    Go long when price closes above the highest high of the last `lookback`
    bars; go short when it closes below the lowest low. It's a different style
    of strategy than the EMA crossover, so you can compare approaches.
    """

    def __init__(self, config: BreakoutConfig) -> None:
        super().__init__(config)
        self.instrument: Instrument | None = None
        # Rolling windows (capped at `lookback`) holding recent bar highs/lows.
        self.highs: deque[float] = deque(maxlen=config.lookback)
        self.lows: deque[float] = deque(maxlen=config.lookback)

    def on_start(self) -> None:
        self.instrument = self.cache.instrument(self.config.instrument_id)
        self.subscribe_bars(self.config.bar_type)

    def on_bar(self, bar: Bar) -> None:
        # Warm up until we have a full channel of `lookback` bars.
        if len(self.highs) < self.config.lookback:
            self.highs.append(bar.high.as_double())
            self.lows.append(bar.low.as_double())
            return

        highest = max(self.highs)
        lowest = min(self.lows)
        close = bar.close.as_double()

        if close > highest:
            if self.portfolio.is_flat(self.config.instrument_id):
                self._submit(OrderSide.BUY)
            elif self.portfolio.is_net_short(self.config.instrument_id):
                self.close_all_positions(self.config.instrument_id)
                self._submit(OrderSide.BUY)
        elif close < lowest:
            if self.portfolio.is_flat(self.config.instrument_id):
                self._submit(OrderSide.SELL)
            elif self.portfolio.is_net_long(self.config.instrument_id):
                self.close_all_positions(self.config.instrument_id)
                self._submit(OrderSide.SELL)

        self.highs.append(bar.high.as_double())
        self.lows.append(bar.low.as_double())

    def _submit(self, side: OrderSide) -> None:
        order = self.order_factory.market(
            instrument_id=self.config.instrument_id,
            order_side=side,
            quantity=self.instrument.make_qty(self.config.trade_size),
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)

    def on_stop(self) -> None:
        self.cancel_all_orders(self.config.instrument_id)
        self.close_all_positions(self.config.instrument_id)
