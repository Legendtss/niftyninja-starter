# =============================================================
#  data/fetcher.py
#  The data layer — all market data comes through here.
#  Nothing else in the project calls yfinance directly.
#  If you ever swap yfinance for Zerodha Kite, you only
#  change this one file and nothing else breaks.
# =============================================================

import yfinance as yf
import pandas as pd
import sys
import os
from datetime import datetime, timedelta
from typing import Optional

# Allow running this file directly: python data/fetcher.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    WATCHLIST, HISTORICAL_YEARS,
    INTRADAY_INTERVAL, INTRADAY_PERIOD
)
from utils.logger import get_logger
from utils.helpers import nse_ticker

log = get_logger("DataFetcher")


class DataFetcher:
    """
    Fetches stock data from Yahoo Finance (via yfinance).

    All methods return either:
      - A pandas DataFrame (for OHLCV history)
      - A dict (for a single quote snapshot)
      - An empty DataFrame / empty dict on failure

    They never raise exceptions — failures are logged and
    an empty result is returned so the rest of the app keeps running.
    """

    # ----------------------------------------------------------
    # Historical daily data
    # ----------------------------------------------------------

    def get_history(
        self,
        symbol: str,
        years: int = HISTORICAL_YEARS,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch daily OHLCV data going back `years` years.

        Returns a DataFrame with columns:
            Open, High, Low, Close, Volume
        Index is a DatetimeIndex (one row per trading day).

        Example:
            df = fetcher.get_history("RELIANCE", years=2)
            print(df.tail())   # last 5 trading days
            print(df["Close"].iloc[-1])   # most recent close
        """
        ticker = nse_ticker(symbol)

        # Build date range
        end_date   = end   or datetime.today().strftime("%Y-%m-%d")
        start_date = start or (
            datetime.today() - timedelta(days=365 * years)
        ).strftime("%Y-%m-%d")

        log.info(f"Fetching history: {ticker} | {start_date} -> {end_date}")

        try:
            df = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                progress=False,      # suppress the download progress bar
                auto_adjust=True,    # adjust for splits and dividends
            )

            if df is None or df.empty:
                log.warning(f"No data returned for {ticker}")
                return pd.DataFrame()

            # yfinance sometimes returns MultiIndex columns — flatten them
            if hasattr(df.columns, "levels"):
                df.columns = df.columns.droplevel(1)

            df.index = pd.to_datetime(df.index)
            df.dropna(inplace=True)

            log.info(f"  Got {len(df)} daily candles for {symbol}")
            return df

        except Exception as e:
            log.error(f"History fetch failed for {ticker}: {e}")
            return pd.DataFrame()

    # ----------------------------------------------------------
    # Intraday data (5m, 15m, 1h candles)
    # ----------------------------------------------------------

    def get_intraday(
        self,
        symbol: str,
        interval: str = INTRADAY_INTERVAL,
        period: str = INTRADAY_PERIOD,
    ) -> pd.DataFrame:
        """
        Fetch intraday OHLCV candles.

        interval: "1m", "5m", "15m", "1h"
        period:   "1d", "5d", "60d"  ← yfinance limit is 60d for intraday

        Note: yfinance limits intraday history:
          - 1m  → max 7 days back
          - 5m  → max 60 days back
          - 15m → max 60 days back
          - 1h  → max 730 days back
        """
        ticker = nse_ticker(symbol)
        log.info(f"Fetching intraday: {ticker} | {interval} | {period}")

        try:
            df = yf.download(
                ticker,
                period=period,
                interval=interval,
                progress=False,
                auto_adjust=True,
            )

            if df is None or df.empty:
                log.warning(f"No intraday data for {ticker}")
                return pd.DataFrame()

            if hasattr(df.columns, "levels"):
                df.columns = df.columns.droplevel(1)

            df.index = pd.to_datetime(df.index)
            df.dropna(inplace=True)
            return df

        except Exception as e:
            log.error(f"Intraday fetch failed for {ticker}: {e}")
            return pd.DataFrame()

    # ----------------------------------------------------------
    # Live quote (current price snapshot)
    # ----------------------------------------------------------

    def get_quote(self, symbol: str) -> dict:
        """
        Get the current price and basic info for one stock.

        Returns a dict like:
        {
            "symbol":     "RELIANCE",
            "price":      2847.50,
            "change":     12.30,
            "change_pct": 0.43,     ← in percent, e.g. 0.43 means 0.43%
            "day_high":   2855.00,
            "day_low":    2830.00,
            "volume":     4523100,
        }

        Returns empty dict on failure — always check before using.
        """
        ticker = nse_ticker(symbol)

        try:
            t    = yf.Ticker(ticker)
            info = t.fast_info   # faster than t.info — less data, less wait

            # yfinance keys changed across versions; support both styles.
            def pick(*keys, default=None):
                for key in keys:
                    value = info.get(key)
                    if value is not None:
                        return value
                return default

            price      = float(pick("last_price", "lastPrice", default=0) or 0)
            prev_close = float(pick(
                "previous_close", "previousClose", "regularMarketPreviousClose", default=price
            ) or price)
            change     = round(price - prev_close, 2)
            change_pct = round((change / prev_close * 100) if prev_close else 0, 2)

            return {
                "symbol":     symbol,
                "price":      round(price, 2),
                "change":     change,
                "change_pct": change_pct,
                "day_high":   float(pick("day_high", "dayHigh", default=0) or 0),
                "day_low":    float(pick("day_low", "dayLow", default=0) or 0),
                "volume":     int(pick("three_month_average_volume", "threeMonthAverageVolume", default=0) or 0),
            }

        except Exception as e:
            log.error(f"Quote fetch failed for {symbol}: {e}")
            return {"symbol": symbol, "price": 0, "change_pct": 0}

    # ----------------------------------------------------------
    # Fetch all watchlist stocks at once
    # ----------------------------------------------------------

    def get_all_quotes(self) -> dict:
        """
        Fetch live quotes for every stock in WATCHLIST.
        Returns a dict:  { "RELIANCE": {...}, "INFY": {...}, ... }
        """
        quotes = {}
        for symbol in WATCHLIST:
            quotes[symbol] = self.get_quote(symbol)
        return quotes

    def get_all_history(self) -> dict:
        """
        Fetch daily history for every stock in WATCHLIST.
        Returns a dict:  { "RELIANCE": DataFrame, "INFY": DataFrame, ... }
        Skips symbols where data is unavailable.
        """
        data = {}
        for symbol in WATCHLIST:
            df = self.get_history(symbol)
            if not df.empty:
                data[symbol] = df
        return data


# -------------------------------------------------------------------
# Quick test — run this file directly to verify data is fetching
# python data/fetcher.py
# -------------------------------------------------------------------
if __name__ == "__main__":
    fetcher = DataFetcher()

    print("\n=== Live Quotes ===")
    quotes = fetcher.get_all_quotes()
    for sym, q in quotes.items():
        arrow = "▲" if q["change_pct"] >= 0 else "▼"
        print(f"  {sym:12s}  ₹{q['price']:>10,.2f}  {arrow} {q['change_pct']:+.2f}%")

    print("\n=== Historical Data (RELIANCE, last 5 rows) ===")
    df = fetcher.get_history("RELIANCE", years=1)
    if not df.empty:
        print(df.tail())
        print(f"\n  Total trading days: {len(df)}")
        print(f"  Columns: {list(df.columns)}")
