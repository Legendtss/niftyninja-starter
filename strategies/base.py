# =============================================================
#  strategies/base.py
#  The base class that every strategy inherits from.
#  Also defines OrderProposal — the object a strategy returns
#  when it finds a trading opportunity.
#
#  Phase 4 of your learning roadmap.
# =============================================================

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from config import MAX_RISK_PER_TRADE, STARTING_CAPITAL
from utils.logger import get_logger

log = get_logger("Strategy")


# -------------------------------------------------------------------
# OrderProposal — what a strategy returns when it finds a signal
# -------------------------------------------------------------------

@dataclass
class OrderProposal:
    """
    An order proposed by a strategy.
    It does NOT execute automatically — it waits for approval.

    Think of it as the strategy saying:
    "I think you should buy X shares of RELIANCE at ₹2847,
     with a stop-loss at ₹2810 and target at ₹2920."

    The human (or auto-executor) then decides whether to act on it.
    """
    symbol:     str
    side:       str      # "BUY" or "SELL"
    quantity:   int
    price:      float
    stop_loss:  Optional[float] = None
    target:     Optional[float] = None
    strategy:   str = ""
    reason:     str = ""
    confidence: int = 0

    def risk_amount(self) -> float:
        """How much money is at risk if stop-loss is hit."""
        if self.stop_loss is None:
            return 0.0
        return abs(self.price - self.stop_loss) * self.quantity

    def reward_amount(self) -> float:
        """Potential profit if target is hit."""
        if self.target is None:
            return 0.0
        return abs(self.target - self.price) * self.quantity

    def risk_reward_ratio(self) -> float:
        """Reward ÷ Risk. Aim for at least 2:1."""
        risk = self.risk_amount()
        if risk == 0:
            return 0.0
        return round(self.reward_amount() / risk, 2)

    def summary(self) -> str:
        """One-line description of the proposal."""
        sl  = f" | SL ₹{self.stop_loss:.2f}"  if self.stop_loss else ""
        tgt = f" | Tgt ₹{self.target:.2f}"    if self.target    else ""
        rr  = f" | R:R {self.risk_reward_ratio():.1f}" if self.stop_loss and self.target else ""
        return (
            f"{self.strategy} → {self.side} {self.quantity}x {self.symbol} "
            f"@ ₹{self.price:.2f}{sl}{tgt}{rr}"
        )


# -------------------------------------------------------------------
# BaseStrategy — inherit from this to create your own strategies
# -------------------------------------------------------------------

class BaseStrategy(ABC):
    """
    All trading strategies inherit from this class.

    To create a new strategy:
    1. Create a new file in strategies/
    2. Import and inherit BaseStrategy
    3. Set a unique `name`
    4. Implement `generate_signal()`

    Example:
        class MyStrategy(BaseStrategy):
            name = "MyStrategy"

            def generate_signal(self, df, symbol):
                # your logic here
                # return an OrderProposal if there's a signal
                # return None if no signal
    """

    # Override this with your strategy's name
    name = "BaseStrategy"

    def __init__(self, capital: float = STARTING_CAPITAL):
        self.capital = capital   # used for position sizing
        self.active  = True      # can be toggled in the dashboard

    @abstractmethod
    def generate_signal(
        self, df: pd.DataFrame, symbol: str
    ) -> Optional[OrderProposal]:
        """
        Look at the data and decide if there's a trade.

        Args:
            df:     OHLCV DataFrame (all candles up to NOW — no future data)
            symbol: The stock being analysed

        Returns:
            OrderProposal if a signal is found
            None if no signal
        """
        pass

    # ----------------------------------------------------------
    # Helper: calculate how many shares to buy
    # ----------------------------------------------------------

    def _position_size(self, price: float, stop_loss: float) -> int:
        """
        Calculate how many shares to buy based on risk management.

        Logic:
          - Never risk more than MAX_RISK_PER_TRADE % of capital
          - Risk per share = price - stop_loss
          - Max shares = (capital * risk_pct) / risk_per_share

        Example:
          capital       = ₹5,00,000
          risk_pct      = 2%  → ₹10,000 max risk
          price         = ₹2847
          stop_loss     = ₹2810
          risk_per_share = ₹37
          max_shares    = 10,000 / 37 = 270 shares
        """
        if price <= 0 or stop_loss <= 0:
            return 1

        risk_per_share  = abs(price - stop_loss)
        if risk_per_share == 0:
            return 1

        max_risk_amount = self.capital * MAX_RISK_PER_TRADE
        quantity        = int(max_risk_amount / risk_per_share)

        return max(1, quantity)   # always at least 1 share

    # ----------------------------------------------------------
    # Helper: calculate ATR for dynamic stop-losses
    # ----------------------------------------------------------

    def _atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        ATR = Average True Range — how much the stock typically moves.
        Use this to set stop-losses that give the trade room to breathe.
        """
        high  = df["High"].squeeze()
        low   = df["Low"].squeeze()
        close = df["Close"].squeeze()

        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low  - close.shift()).abs(),
        ], axis=1).max(axis=1)

        atr = float(tr.rolling(period).mean().iloc[-1])
        return max(atr, 0.01)   # never return 0
