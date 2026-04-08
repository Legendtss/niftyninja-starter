# =============================================================
#  strategies/rsi_strategy.py
#  Your first complete trading strategy.
#
#  Logic:
#    Buy when:  RSI < 35 (oversold) AND price above SMA200 (uptrend)
#    Stop-loss: 1.5x ATR below entry
#    Target:    3x ATR above entry (2:1 reward:risk)
#
#  This is the "buy the dip in an uptrend" strategy.
#  It does NOT work in downtrends — the SMA200 filter helps.
# =============================================================

import pandas as pd
import numpy as np
from typing import Optional

from strategies.base import BaseStrategy, OrderProposal
from utils.logger import get_logger

log = get_logger("RSIStrategy")


class RSIStrategy(BaseStrategy):
    """
    Simple RSI mean-reversion strategy.

    Entry conditions (ALL must be true):
      1. RSI falls below 35 — stock is oversold
      2. Price is above SMA200 — long-term uptrend (don't buy falling knives)
      3. RSI was above 35 in the last 5 candles — fresh dip, not a trend

    Exit:
      Stop-loss:  1.5 × ATR below entry
      Target:     3.0 × ATR above entry
      Risk:Reward = 2:1 minimum
    """

    name = "RSIStrategy"

    def generate_signal(
        self, df: pd.DataFrame, symbol: str
    ) -> Optional[OrderProposal]:
        """
        Check if all conditions are met and return an OrderProposal.
        Returns None if no signal.
        """

        # Need enough data for all calculations
        if len(df) < 210:   # 200 days for SMA200 + buffer
            return None

        try:
            close = df["Close"].squeeze()
            price = float(close.iloc[-1])

            # --- Calculate RSI ---
            delta = close.diff()
            gain  = delta.clip(lower=0).rolling(14).mean()
            loss  = (-delta).clip(lower=0).rolling(14).mean()
            rs    = gain / loss.replace(0, np.nan)
            rsi   = 100 - (100 / (1 + rs))

            current_rsi = float(rsi.iloc[-1])
            rsi_5d_max  = float(rsi.iloc[-6:-1].max())   # max RSI in last 5 candles

            # --- Calculate SMA200 ---
            sma200 = float(close.rolling(200).mean().iloc[-1])

            # --- Calculate ATR for stop-loss/target ---
            atr = self._atr(df)

            # -----------------------------------------------
            # Entry conditions — ALL must be true
            # -----------------------------------------------
            rsi_oversold = current_rsi < 35
            in_uptrend   = price > sma200               # only buy in uptrends
            fresh_dip    = rsi_5d_max > 40              # RSI was higher recently

            if not (rsi_oversold and in_uptrend and fresh_dip):
                return None   # conditions not met — no signal

            # -----------------------------------------------
            # Calculate stop-loss and target
            # -----------------------------------------------
            stop_loss = round(price - (1.5 * atr), 2)
            target    = round(price + (3.0 * atr), 2)

            # Calculate how many shares to buy based on risk
            quantity = self._position_size(price, stop_loss)

            log.info(
                f"RSIStrategy signal on {symbol}: "
                f"RSI={current_rsi:.1f} | Price=₹{price:.2f} | "
                f"SMA200=₹{sma200:.2f} | ATR=₹{atr:.2f}"
            )

            return OrderProposal(
                symbol     = symbol,
                side       = "BUY",
                quantity   = quantity,
                price      = price,
                stop_loss  = stop_loss,
                target     = target,
                strategy   = self.name,
                reason     = (
                    f"RSI oversold at {current_rsi:.1f} | "
                    f"Price ₹{price:.2f} above SMA200 ₹{sma200:.2f}"
                ),
                confidence = 65,
            )

        except Exception as e:
            log.error(f"RSIStrategy error on {symbol}: {e}")
            return None
