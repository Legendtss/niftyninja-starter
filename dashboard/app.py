# =============================================================
#  dashboard/app.py
#  The main Streamlit dashboard.
#  Start here — this is what you'll run every day.
#
#  Run with:  streamlit run dashboard/app.py
#  Opens at:  http://localhost:8501
#
#  Phase 7 of your learning roadmap.
#  Right now it shows live prices and signals.
#  You'll add more as you build more modules.
# =============================================================

import sys
import os

# Add project root to Python path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd

from data.fetcher import DataFetcher
from signals.engine import SignalEngine
from config import WATCHLIST, STARTING_CAPITAL
from utils.helpers import format_inr, pct

# --- Page configuration --------------------------------------
st.set_page_config(
    page_title   = "NiftyNinja",
    page_icon    = "🥷",
    layout       = "wide",
    initial_sidebar_state = "expanded",
)

# --- Initialise modules (once per session) -------------------
# st.cache_resource keeps these alive across reruns
@st.cache_resource
def get_fetcher():
    return DataFetcher()

@st.cache_resource
def get_engine():
    return SignalEngine()

fetcher = get_fetcher()
engine  = get_engine()


# =============================================================
# SIDEBAR
# =============================================================
with st.sidebar:
    st.markdown("## 🥷 NiftyNinja")
    st.caption("Paper trading assistant")
    st.divider()

    # Portfolio summary (placeholder — real values come in Phase 6)
    st.metric("Capital",    format_inr(STARTING_CAPITAL))
    st.metric("Today P&L",  "₹0.00")
    st.metric("Open Positions", "0")

    st.divider()

    # Let user pick up to 5 stocks for live prices to keep the view readable.
    live_symbols = st.multiselect(
        "Live Prices (up to 5)",
        options=WATCHLIST,
        default=WATCHLIST[:5],
        max_selections=5,
    )

    st.divider()

    # Manual refresh button
    if st.button("🔄 Refresh prices", use_container_width=True):
        st.cache_data.clear()   # force fresh data on next fetch
        st.rerun()

    st.caption("Prices from Yahoo Finance (~15 min delay)")


# =============================================================
# MAIN AREA
# =============================================================
st.markdown("## Live Prices")

# Fetch quotes for selected stocks
quotes = {}
if live_symbols:
    with st.spinner("Fetching prices..."):
        for sym in live_symbols:
            quotes[sym] = fetcher.get_quote(sym)
else:
    st.info("Select up to 5 symbols in the sidebar to show live prices.")

# Display as a clean metrics grid
if quotes:
    cols = st.columns(len(quotes))
    for i, (sym, q) in enumerate(quotes.items()):
        price = q.get("price", 0)
        chg   = q.get("change_pct", 0)
        delta_str = f"{chg:+.2f}%"
        cols[i].metric(
            label = sym,
            value = f"₹{price:,.2f}",
            delta = delta_str,
        )

st.divider()

# =============================================================
# SIGNALS TABLE
# =============================================================
st.markdown("## Technical Signals")
st.caption("Computed from daily data. Not financial advice.")

if WATCHLIST:
    with st.spinner("Computing signals..."):
        rows = []
        for sym in WATCHLIST:
            # Get historical data and run signal engine
            df = fetcher.get_history(sym, years=1)
            if df.empty:
                continue

            result = engine.analyse(df, sym)
            ind    = result.get("indicators", {})

            rows.append({
                "Symbol":     sym,
                "Signal":     result.get("overall", "NEUTRAL"),
                "Confidence": result.get("confidence", 0),
                "RSI":        ind.get("rsi", 0),
                "MACD":       "Bullish" if ind.get("macd_bullish") else "Bearish",
                "Vol Ratio":  f"{ind.get('volume_ratio', 1):.1f}x",
                "SMA200":     "Above" if ind.get("above_sma200") else "Below",
                "BB%":        ind.get("bb_pct", 50),
            })

    if rows:
        df_signals = pd.DataFrame(rows)
        df_signals.index = range(1, len(df_signals) + 1)
        df_signals.index.name = "#"
        st.dataframe(
            df_signals,
            use_container_width=True,
            column_config={
                "Confidence": st.column_config.ProgressColumn(
                    "Confidence",
                    min_value=0,
                    max_value=100,
                    format="%d%%",
                ),
                "BB%": st.column_config.ProgressColumn(
                    "BB Position",
                    min_value=0,
                    max_value=100,
                    format="%d%%",
                ),
            }
        )

        # Show alerts if any
        all_alerts = []
        for sym in WATCHLIST:
            df = fetcher.get_history(sym, years=1)
            if df.empty:
                continue
            result = engine.analyse(df, sym)
            for alert in result.get("alerts", []):
                all_alerts.append({
                    "stock":   sym,
                    "level":   alert["level"],
                    "message": alert["message"],
                })

        if all_alerts:
            st.divider()
            st.markdown("### Alerts")
            for a in all_alerts:
                icon = "🔴" if a["level"] == "high" else "🟡"
                st.markdown(f"{icon} **{a['stock']}** — {a['message']}")

st.divider()

# =============================================================
# PLACEHOLDER SECTIONS (you'll fill these in as you build)
# =============================================================
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 📋 Open Positions")
    st.info("Paper trade engine coming in Phase 6")

with col_right:
    st.markdown("### 📰 News Feed")
    st.info("News fetcher coming in Phase 10")

# Footer
st.caption("NiftyNinja — Paper trading only. Not financial advice.")
