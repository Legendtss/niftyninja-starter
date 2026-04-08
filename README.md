# 🥷 NiftyNinja

AI-assisted paper trading system for the Indian stock market.
Built step by step — this is the starter version.

---

## What's in this starter

| File | What it does |
|------|-------------|
| `config.py` | All settings — your watchlist, capital, risk limits |
| `data/fetcher.py` | Fetches live and historical NSE prices via yfinance |
| `signals/engine.py` | Computes RSI, MACD, Bollinger Bands, Volume signals |
| `strategies/base.py` | Base class all strategies inherit from |
| `strategies/rsi_strategy.py` | First complete strategy (RSI oversold + uptrend) |
| `dashboard/app.py` | Streamlit web dashboard — run this to see everything |
| `main.py` | Menu launcher — start here |
| `utils/logger.py` | Coloured logging to terminal and file |
| `utils/helpers.py` | Small utility functions (format_inr, is_market_open etc.) |

**What's not here yet** (you'll build these phase by phase):
- Paper trade execution engine + SQLite database
- Backtester
- News fetcher
- Bot runner (background thread)
- Training mode (Time Machine)

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/niftyninja.git
cd niftyninja
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Activate it — do this every time you open a terminal
source venv/bin/activate      # Mac / Linux
venv\Scripts\activate         # Windows
```

> You'll know it's active when you see `(venv)` in your terminal prompt.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Copy the environment file

```bash
cp .env.example .env
```

No secrets are needed right now — the project works without any API keys.

### 5. Run it

```bash
# Option A: Menu launcher (easiest)
python main.py

# Option B: Dashboard directly
streamlit run dashboard/app.py

# Option C: Test individual modules
python data/fetcher.py       # verify prices are fetching
python signals/engine.py     # verify signals are computing
python utils/helpers.py      # verify helpers work
```

---

## How to contribute (for teammates)

### Branch naming

```
feature/phase-05-backtester
feature/phase-06-paper-engine
fix/rsi-calculation-bug
```

### Workflow

```bash
# Always pull latest before starting work
git pull origin main

# Create a branch for your feature
git checkout -b feature/your-feature-name

# Make your changes, then commit
git add .
git commit -m "Add: RSI strategy unit tests"

# Push and open a pull request
git push origin feature/your-feature-name
```

### Pull Request rules

- One feature per PR
- Run the module's quick test before pushing (`python data/fetcher.py`)
- Add a comment explaining what changed and why

---

## Project structure

```
niftyninja/
│
├── config.py                ← START HERE — all settings
├── main.py                  ← menu launcher
├── requirements.txt         ← pip install -r requirements.txt
├── .env.example             ← copy to .env, fill in secrets
├── .gitignore
│
├── data/
│   ├── __init__.py
│   └── fetcher.py           ← yfinance wrapper (Phase 1–2)
│
├── signals/
│   ├── __init__.py
│   └── engine.py            ← RSI, MACD, BB, Volume (Phase 3–4)
│
├── strategies/
│   ├── __init__.py
│   ├── base.py              ← OrderProposal + BaseStrategy
│   └── rsi_strategy.py      ← first strategy (Phase 4)
│
├── paper_engine/            ← TODO Phase 6
│   └── __init__.py
│
├── dashboard/
│   ├── __init__.py
│   └── app.py               ← Streamlit UI (Phase 7)
│
├── utils/
│   ├── __init__.py
│   ├── logger.py            ← coloured logging
│   └── helpers.py           ← format_inr, is_market_open etc.
│
├── db/                      ← SQLite files go here (gitignored)
└── logs/                    ← log files go here (gitignored)
```

---

## What to build next

Follow the phase roadmap. Each phase has a clear milestone — don't move on until you can pass it.

| Phase | What you build | File to create |
|-------|---------------|----------------|
| 5 | Backtester | `backtester/engine.py` |
| 6 | Paper trade engine + SQLite | `paper_engine/executor.py` |
| 7 | Streamlit charts (Plotly) | Update `dashboard/app.py` |
| 8 | Plotly candlestick chart | Update `dashboard/app.py` |
| 9 | Bot runner (background thread) | `bot_runner/runner.py` |
| 10 | News fetcher (RSS) | `news/fetcher.py` |
| 11–12 | Time Machine training mode | `training/time_machine.py` |

---

## Adding a new strategy

Create a file in `strategies/`:

```python
# strategies/my_strategy.py
from strategies.base import BaseStrategy, OrderProposal
from typing import Optional
import pandas as pd

class MyStrategy(BaseStrategy):
    name = "MyStrategy"

    def generate_signal(
        self, df: pd.DataFrame, symbol: str
    ) -> Optional[OrderProposal]:
        # your logic here
        # return OrderProposal(...) if signal found
        # return None if no signal
        pass
```

Then add it to `config.py`:
```python
ACTIVE_STRATEGIES = [
    "RSIStrategy",
    "MyStrategy",   # ← add here
]
```

---

## Common issues

**`ModuleNotFoundError: No module named 'yfinance'`**
You forgot to activate the virtual environment.
```bash
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

**`streamlit: command not found`**
```bash
pip install streamlit
```

**`No data returned for RELIANCE.NS`**
yfinance sometimes has rate limits. Wait 30 seconds and try again.
Or check your internet connection.

**Prices look wrong or delayed**
yfinance data has a 15–20 minute delay. This is normal for the free feed.
Real-time data requires Zerodha Kite Connect (Phase 12).

---

## Tech stack

| Library | Purpose |
|---------|---------|
| Python 3.11 | Language |
| yfinance | NSE/BSE data (free) |
| pandas | DataFrames — all data manipulation |
| numpy | Math operations |
| pandas-ta | RSI, MACD, Bollinger Bands (130+ indicators) |
| Streamlit | Web dashboard |
| Plotly | Interactive charts |
| requests | HTTP calls |
| feedparser | RSS news feeds |
| colorama | Coloured terminal output |

---

*NiftyNinja — Paper trading only. Not financial advice. Use responsibly.*
