# =============================================================
#  signals/engine.py
#  Computes technical indicators and generates signals.
#
#  This is a pure calculation module — it takes a DataFrame in
#  and returns results out. It never fetches data or places orders.
#
#  Phase 3-4 of your learning roadmap.
# =============================================================

import pandas as pd
import numpy as np
from typing import Optional

from config import RSI_OVERSOLD, RSI_OVERBOUGHT, VOLUME_SPIKE
from utils.logger import get_logger

log = get_logger("SignalEngine")

# Try to import pandas-ta — fall back to manual calculations if not installed yet
try:
    import pandas_ta as ta
    USE_PANDAS_TA = True
except ImportError:
    USE_PANDAS_TA = False
    log.warning("pandas-ta not installed. Using manual indicator calculations.")
    log.warning("Run: pip install pandas-ta")


class SignalEngine:
    """
    Computes all technical indicators for a given OHLCV DataFrame.

    Usage:
        engine = SignalEngine()
        result = engine.analyse(df, "RELIANCE")
        print(result["overall"])      # "BUY", "SELL", or "NEUTRAL"
        print(result["indicators"])   # dict of RSI, MACD, etc.
        print(result["signals"])      # list of triggered signals
        print(result["alerts"])       # list of notable events
    """

    def analyse(self, df: pd.DataFrame, symbol: str = "") -> dict:
        """
        Run all indicators on the DataFrame and return a full report.

        Input:  df with columns Open, High, Low, Close, Volume
        Output: dict with overall signal, indicators, signals list, alerts list
        """
        if df is None or df.empty or len(df) < 30:
            return {
                "symbol": symbol,
                "error":  "Need at least 30 candles of data",
                "overall": "NEUTRAL",
                "confidence": 0,
                "indicators": {},
                "signals": [],
                "alerts": [],
            }

        df = df.copy()  # never modify the original

        result = {
            "symbol":     symbol,
            "overall":    "NEUTRAL",
            "confidence": 40,
            "indicators": {},
            "signals":    [],
            "alerts":     [],
        }

        # Compute each indicator group
        result["indicators"].update(self._rsi(df))
        result["indicators"].update(self._macd(df))
        result["indicators"].update(self._bollinger(df))
        result["indicators"].update(self._volume(df))
        result["indicators"].update(self._moving_averages(df))
        result["indicators"].update(self._atr(df))

        # Combine indicators into signals
        self._generate_signals(result)

        return result

    # ----------------------------------------------------------
    # RSI — Relative Strength Index
    # ----------------------------------------------------------

    def _rsi(self, df: pd.DataFrame, period: int = 14) -> dict:
        """
        RSI measures momentum on a 0–100 scale.
        Below 35 = stock may be oversold (potential buy).
        Above 65 = stock may be overbought (potential sell).
        """
        close = df["Close"].squeeze()

        if USE_PANDAS_TA:
            rsi_series = ta.rsi(close, length=period)
        else:
            # Manual RSI calculation — good to understand
            delta    = close.diff()
            gain     = delta.clip(lower=0).rolling(period).mean()
            loss     = (-delta).clip(lower=0).rolling(period).mean()
            rs       = gain / loss.replace(0, np.nan)
            rsi_series = 100 - (100 / (1 + rs))

        current = float(rsi_series.iloc[-1]) if rsi_series is not None else 50
        prev    = float(rsi_series.iloc[-2]) if len(rsi_series) > 1 else 50

        return {
            "rsi":      round(current, 2),
            "rsi_prev": round(prev, 2),
            "rsi_dir":  "rising" if current > prev else "falling",
        }

    # ----------------------------------------------------------
    # MACD — Moving Average Convergence Divergence
    # ----------------------------------------------------------

    def _macd(self, df: pd.DataFrame) -> dict:
        """
        MACD shows trend direction and momentum.
        When MACD crosses above the signal line → bullish.
        When MACD crosses below the signal line → bearish.
        The histogram is MACD minus signal line.
        """
        close = df["Close"].squeeze()

        if USE_PANDAS_TA:
            macd_df = ta.macd(close, fast=12, slow=26, signal=9)
            if macd_df is not None and not macd_df.empty:
                macd_line   = float(macd_df.iloc[-1, 0])
                signal_line = float(macd_df.iloc[-1, 1])
                histogram   = float(macd_df.iloc[-1, 2])
                prev_hist   = float(macd_df.iloc[-2, 2]) if len(macd_df) > 1 else 0
            else:
                macd_line = signal_line = histogram = prev_hist = 0
        else:
            # Manual MACD
            ema12       = close.ewm(span=12).mean()
            ema26       = close.ewm(span=26).mean()
            macd_line   = float((ema12 - ema26).iloc[-1])
            signal_line = float((ema12 - ema26).ewm(span=9).mean().iloc[-1])
            histogram   = macd_line - signal_line
            prev_hist   = float(
                ((ema12 - ema26) - (ema12 - ema26).ewm(span=9).mean()).iloc[-2]
            )

        return {
            "macd":          round(macd_line, 3),
            "macd_signal":   round(signal_line, 3),
            "macd_hist":     round(histogram, 3),
            "macd_bullish":  macd_line > signal_line,
            # Crossover = histogram just flipped from negative to positive
            "macd_crossover":  histogram > 0 and prev_hist <= 0,
            "macd_crossunder": histogram < 0 and prev_hist >= 0,
        }

    # ----------------------------------------------------------
    # Bollinger Bands
    # ----------------------------------------------------------

    def _bollinger(self, df: pd.DataFrame, period: int = 20) -> dict:
        """
        Bollinger Bands = SMA ± 2 standard deviations.
        Price below lower band → possible oversold (buy signal).
        Price above upper band → possible overbought (sell signal).
        Very narrow bands (squeeze) → big move coming soon.
        """
        close = df["Close"].squeeze()
        price = float(close.iloc[-1])

        if USE_PANDAS_TA:
            bb = ta.bbands(close, length=period, std=2)
            if bb is not None and not bb.empty:
                upper  = float(bb.iloc[-1, 0])
                mid    = float(bb.iloc[-1, 1])
                lower  = float(bb.iloc[-1, 2])
            else:
                upper = mid = lower = price
        else:
            sma   = close.rolling(period).mean()
            std   = close.rolling(period).std()
            upper = float((sma + 2 * std).iloc[-1])
            mid   = float(sma.iloc[-1])
            lower = float((sma - 2 * std).iloc[-1])

        width = (upper - lower) / mid if mid else 0

        # BB position: 0% = at lower band, 100% = at upper band
        bb_pct = round(
            (price - lower) / (upper - lower) * 100, 1
        ) if upper != lower else 50

        return {
            "bb_upper":       round(upper, 2),
            "bb_mid":         round(mid, 2),
            "bb_lower":       round(lower, 2),
            "bb_width":       round(width, 4),
            "bb_pct":         bb_pct,
            "bb_squeeze":     width < 0.02,
            "above_bb_upper": price > upper,
            "below_bb_lower": price < lower,
        }

    # ----------------------------------------------------------
    # Volume
    # ----------------------------------------------------------

    def _volume(self, df: pd.DataFrame) -> dict:
        """
        Compare today's volume to the 20-day average.
        A spike (2x+ the average) confirms a price move is real.
        Low volume = weak signal, may not follow through.
        """
        vol      = df["Volume"].squeeze()
        current  = float(vol.iloc[-1])
        avg_20   = float(vol.rolling(20).mean().iloc[-1])
        ratio    = round(current / avg_20, 2) if avg_20 > 0 else 1

        return {
            "volume":       int(current),
            "volume_avg20": int(avg_20),
            "volume_ratio": ratio,
            "volume_spike": ratio >= VOLUME_SPIKE,
        }

    # ----------------------------------------------------------
    # Moving Averages
    # ----------------------------------------------------------

    def _moving_averages(self, df: pd.DataFrame) -> dict:
        """
        SMA = Simple Moving Average (equal weight to all candles)
        EMA = Exponential Moving Average (more weight on recent candles)

        Price > SMA200 = long-term uptrend.
        SMA50 crosses above SMA200 = "golden cross" (very bullish).
        SMA50 crosses below SMA200 = "death cross" (very bearish).
        """
        close = df["Close"].squeeze()
        price = float(close.iloc[-1])

        sma20  = float(close.rolling(20).mean().iloc[-1])
        sma50  = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else sma20
        sma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else sma50

        return {
            "sma20":       round(sma20, 2),
            "sma50":       round(sma50, 2),
            "sma200":      round(sma200, 2),
            "above_sma20": price > sma20,
            "above_sma50": price > sma50,
            "above_sma200":price > sma200,
            "golden_cross":sma50 > sma200,
            "death_cross": sma50 < sma200,
        }

    # ----------------------------------------------------------
    # ATR — Average True Range
    # ----------------------------------------------------------

    def _atr(self, df: pd.DataFrame, period: int = 14) -> dict:
        """
        ATR measures volatility — how much the stock typically moves per candle.
        Used to set stop-losses at a distance that gives the trade room to breathe.
        Example: if ATR = ₹25, set stop-loss 1.5x ATR = ₹37.50 below entry.
        """
        high  = df["High"].squeeze()
        low   = df["Low"].squeeze()
        close = df["Close"].squeeze()

        if USE_PANDAS_TA:
            atr_series = ta.atr(high, low, close, length=period)
            atr = float(atr_series.iloc[-1]) if atr_series is not None else 0
        else:
            tr = pd.concat([
                high - low,
                (high - close.shift()).abs(),
                (low  - close.shift()).abs(),
            ], axis=1).max(axis=1)
            atr = float(tr.rolling(period).mean().iloc[-1])

        price = float(close.iloc[-1])
        return {
            "atr":     round(atr, 2),
            "atr_pct": round(atr / price * 100, 2) if price else 0,
        }

    # ----------------------------------------------------------
    # Signal generation — combine indicators into a verdict
    # ----------------------------------------------------------

    def _generate_signals(self, result: dict):
        """
        Look at all the indicators and decide what they mean together.
        More indicators agreeing = higher confidence.
        """
        ind     = result["indicators"]
        signals = result["signals"]
        alerts  = result["alerts"]

        rsi = ind.get("rsi", 50)

        # RSI signals
        if rsi < RSI_OVERSOLD:
            signals.append({
                "type":     "BUY",
                "reason":   f"RSI oversold at {rsi:.1f}",
                "strength": "medium",
            })
        elif rsi > RSI_OVERBOUGHT:
            signals.append({
                "type":     "SELL",
                "reason":   f"RSI overbought at {rsi:.1f}",
                "strength": "medium",
            })

        # MACD crossover signals
        if ind.get("macd_crossover"):
            signals.append({
                "type":     "BUY",
                "reason":   "MACD bullish crossover",
                "strength": "strong",
            })
            alerts.append({
                "level":   "high",
                "message": "MACD just crossed bullish — momentum shifting up",
            })

        if ind.get("macd_crossunder"):
            signals.append({
                "type":     "SELL",
                "reason":   "MACD bearish crossunder",
                "strength": "strong",
            })
            alerts.append({
                "level":   "high",
                "message": "MACD just crossed bearish — momentum shifting down",
            })

        # Bollinger Band signals
        if ind.get("below_bb_lower"):
            signals.append({
                "type":     "BUY",
                "reason":   "Price below lower Bollinger Band",
                "strength": "medium",
            })
        if ind.get("above_bb_upper"):
            signals.append({
                "type":     "SELL",
                "reason":   "Price above upper Bollinger Band",
                "strength": "medium",
            })

        # Bollinger squeeze alert
        if ind.get("bb_squeeze"):
            alerts.append({
                "level":   "medium",
                "message": "Bollinger Band squeeze — big move may be coming",
            })

        # Volume spike alert
        if ind.get("volume_spike"):
            ratio = ind.get("volume_ratio", 1)
            alerts.append({
                "level":   "high",
                "message": f"Volume spike — {ratio:.1f}x the 20-day average",
            })

        # Tally up and set overall verdict
        buy_count  = sum(1 for s in signals if s["type"] == "BUY")
        sell_count = sum(1 for s in signals if s["type"] == "SELL")

        if buy_count >= 2:
            result["overall"]    = "STRONG BUY"
            result["confidence"] = min(90, 50 + buy_count * 15)
        elif buy_count == 1:
            result["overall"]    = "BUY"
            result["confidence"] = 55
        elif sell_count >= 2:
            result["overall"]    = "STRONG SELL"
            result["confidence"] = min(90, 50 + sell_count * 15)
        elif sell_count == 1:
            result["overall"]    = "SELL"
            result["confidence"] = 55
        else:
            result["overall"]    = "NEUTRAL"
            result["confidence"] = 40


# -------------------------------------------------------------------
# Quick test — run this file directly
# python signals/engine.py
# -------------------------------------------------------------------
if __name__ == "__main__":
    from data.fetcher import DataFetcher

    fetcher = DataFetcher()
    engine  = SignalEngine()

    for sym in ["RELIANCE", "INFY", "TCS"]:
        df = fetcher.get_history(sym, years=1)
        if df.empty:
            print(f"  {sym}: No data")
            continue

        result = engine.analyse(df, sym)
        print(f"\n{'='*50}")
        print(f"  {sym} → {result['overall']}  (confidence: {result['confidence']}%)")
        print(f"  RSI: {result['indicators'].get('rsi', 0):.1f}  |  "
              f"MACD: {'bullish' if result['indicators'].get('macd_bullish') else 'bearish'}  |  "
              f"Vol: {result['indicators'].get('volume_ratio', 1):.1f}x")
        for sig in result["signals"]:
            print(f"  [{sig['type']:4s}] {sig['reason']}")
        for alert in result["alerts"]:
            print(f"  [ALERT] {alert['message']}")
