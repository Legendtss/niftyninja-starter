# =============================================================
#  NiftyNinja — config.py
#  All project settings live here.
#  This is the first file you edit when you set up the project.
# =============================================================

# --- Watchlist -----------------------------------------------
# Stocks the bot will track. Add or remove any NSE symbol here.
# yfinance will automatically append ".NS" — don't add it here.
WATCHLIST = [
    "RELIANCE",
    "INFY",
    "TCS",
    "HDFCBANK",
    "SBIN",
]

# --- Capital -------------------------------------------------
# Fake money for paper trading. Change this to whatever you like.
STARTING_CAPITAL = 500_000   # ₹5,00,000

# --- Risk management -----------------------------------------
# These limits protect you from blowing up the account.
MAX_RISK_PER_TRADE = 0.02    # max 2% of capital at risk per trade
MAX_DAILY_LOSS     = 0.05    # stop all trading if down 5% in a day
MAX_OPEN_POSITIONS = 5       # never hold more than 5 positions

# --- Signal thresholds ---------------------------------------
RSI_OVERSOLD   = 35          # RSI below this → potential buy signal
RSI_OVERBOUGHT = 65          # RSI above this → potential sell signal
VOLUME_SPIKE   = 2.0         # alert if volume is 2x the 20-day average

# --- Data settings -------------------------------------------
NSE_SUFFIX        = ".NS"    # appended to symbols for yfinance
HISTORICAL_YEARS  = 2        # years of data to fetch for backtesting
INTRADAY_INTERVAL = "15m"    # candle size: 1m / 5m / 15m / 1h / 1d
INTRADAY_PERIOD   = "60d"    # how far back for intraday data

# --- Execution simulation ------------------------------------
SLIPPAGE_PCT   = 0.001       # 0.1% slippage on fills (realistic)
BROKERAGE      = 20          # ₹20 flat per order (Zerodha-style)
STT_PCT        = 0.001       # Securities Transaction Tax 0.1%

# --- Database ------------------------------------------------
DB_PATH = "db/niftyninja.db" # SQLite file — created automatically

# --- Logging -------------------------------------------------
LOG_LEVEL = "INFO"
LOG_FILE  = "logs/niftyninja.log"

# --- Human confirmation gate ---------------------------------
# True  → bot proposes orders, you approve before execution
# False → bot executes automatically (full auto mode)
REQUIRE_CONFIRMATION = True

# --- Active strategies ---------------------------------------
# Comment out any strategy you don't want running
ACTIVE_STRATEGIES = [
    "RSIStrategy",
    # "BreakoutStrategy",   # uncomment when you build it
]
