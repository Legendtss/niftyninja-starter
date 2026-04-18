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
import plotly.graph_objects as go

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

LIVE_PRICE_SLOT_COUNT = 5
DEFAULT_LIVE_SYMBOLS = WATCHLIST[:LIVE_PRICE_SLOT_COUNT]
CHART_INTERVAL = "5m"
CHART_PERIOD = "5d"


def init_live_price_slots():
    for index in range(LIVE_PRICE_SLOT_COUNT):
        key = f"live_price_slot_{index + 1}"
        if key not in st.session_state:
            st.session_state[key] = DEFAULT_LIVE_SYMBOLS[index] if index < len(DEFAULT_LIVE_SYMBOLS) else ""


def get_live_price_symbols() -> list[str]:
    used_symbols = set()
    live_symbols = []

    for index in range(LIVE_PRICE_SLOT_COUNT):
        key = f"live_price_slot_{index + 1}"
        current_value = st.session_state.get(key, "")

        options = [""] + [symbol for symbol in WATCHLIST if symbol not in used_symbols or symbol == current_value]
        if current_value not in options:
            current_value = ""
            st.session_state[key] = ""

        selected = st.selectbox(
            f"Slot {index + 1}",
            options=options,
            key=key,
        )

        if selected:
            used_symbols.add(selected)
            live_symbols.append(selected)

    return live_symbols


@st.cache_data(ttl=300, show_spinner=False)
def get_chart_data(symbol: str) -> pd.DataFrame:
    return fetcher.get_intraday(symbol, interval=CHART_INTERVAL, period=CHART_PERIOD)


def render_candlestick_chart(df: pd.DataFrame, symbol: str):
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                increasing_line_color="#2ecc71",
                increasing_fillcolor="#2ecc71",
                decreasing_line_color="#e74c3c",
                decreasing_fillcolor="#e74c3c",
                name=symbol,
            )
        ]
    )

    fig.update_layout(
        title=f"{symbol} - 5 Minute Candlestick Chart",
        xaxis_rangeslider_visible=False,
        height=520,
        margin=dict(l=20, r=20, t=50, b=20),
        template="plotly_dark",
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)


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

    # Manual refresh button
    if st.button("🔄 Refresh prices", use_container_width=True):
        st.cache_data.clear()   # force fresh data on next fetch
        st.rerun()

    st.caption("Prices from Yahoo Finance (~15 min delay)")


# =============================================================
# MAIN AREA
# =============================================================
init_live_price_slots()

with st.expander("Configure Live Prices", expanded=False):
    st.caption("Choose up to five stocks. Change the slot order to reorder the cards, or clear a slot to remove a stock.")
    live_symbols = get_live_price_symbols()

st.markdown("## Live Prices")

# Fetch quotes for the configured live-price subset
quotes = {}
with st.spinner("Fetching prices..."):
    for sym in live_symbols:
        quotes[sym] = fetcher.get_quote(sym)

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
# STOCK CHARTS
# =============================================================
st.markdown("## Stock Chart")
st.caption("Choose one stock at a time. Select None to hide the chart.")

chart_choice = st.radio(
    "Select a stock",
    options=["None"] + WATCHLIST,
    horizontal=True,
    index=0,
    key="chart_stock_selector",
)

if chart_choice != "None":
    chart_df = get_chart_data(chart_choice)

    if chart_df.empty:
        st.info(f"No 5-minute chart data available for {chart_choice} right now.")
    else:
        render_candlestick_chart(chart_df, chart_choice)
else:
    st.info("Select any stock above to display its 5-minute candlestick chart.")

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
