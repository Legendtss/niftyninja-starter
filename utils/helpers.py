# =============================================================
#  utils/helpers.py
#  Small utility functions used across the whole project.
#  Nothing complex — just things you'd otherwise copy-paste.
# =============================================================

from datetime import datetime
import pytz


def nse_ticker(symbol: str) -> str:
    """
    Convert a plain NSE symbol to the format yfinance expects.
    Example:  "RELIANCE"  →  "RELIANCE.NS"
              "INFY.NS"   →  "INFY.NS"  (already correct, no double suffix)
    """
    from config import NSE_SUFFIX
    if symbol.endswith(NSE_SUFFIX):
        return symbol
    return symbol + NSE_SUFFIX


def format_inr(amount: float) -> str:
    """
    Format a number as Indian Rupees with the ₹ symbol.
    Uses Indian numbering system (lakhs, crores).
    Example:  1234567.89  →  "₹12,34,567.89"
             -5000.00     →  "-₹5,000.00"
    """
    negative = amount < 0
    amount   = abs(round(amount, 2))

    # Split into integer and decimal
    integer_part = int(amount)
    decimal_part = round(amount - integer_part, 2)
    decimal_str  = f"{decimal_part:.2f}"[1:]  # ".89"

    # Indian numbering: last 3 digits, then groups of 2
    s = str(integer_part)
    if len(s) > 3:
        last3  = s[-3:]
        rest   = s[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        integer_formatted = ",".join(groups) + "," + last3
    else:
        integer_formatted = s

    result = f"₹{integer_formatted}{decimal_str}"
    return f"-{result}" if negative else result


def pct(value: float, decimals: int = 2) -> str:
    """
    Format a decimal as a percentage string with sign.
    Example:  0.0524  →  "+5.24%"
             -0.012   →  "-1.20%"
    """
    sign = "+" if value >= 0 else ""
    return f"{sign}{value * 100:.{decimals}f}%"


def is_market_open() -> bool:
    """
    Check if NSE is currently open.
    Market hours: Monday–Friday, 9:15 AM to 3:30 PM IST.
    Returns True if open right now, False otherwise.
    """
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)

    # Weekend check
    if now.weekday() >= 5:   # 5=Saturday, 6=Sunday
        return False

    # Time check
    open_time  = now.replace(hour=9,  minute=15, second=0, microsecond=0)
    close_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return open_time <= now <= close_time


def current_ist() -> str:
    """Return current IST time as a readable string."""
    ist = pytz.timezone("Asia/Kolkata")
    return datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S IST")


# -------------------------------------------------------------------
# Quick test — run this file directly to verify everything works
# python utils/helpers.py
# -------------------------------------------------------------------
if __name__ == "__main__":
    print(nse_ticker("RELIANCE"))       # RELIANCE.NS
    print(nse_ticker("INFY.NS"))        # INFY.NS  (no double suffix)
    print(format_inr(1234567.89))       # ₹12,34,567.89
    print(format_inr(-5000))            # -₹5,000.00
    print(pct(0.0524))                  # +5.24%
    print(pct(-0.012))                  # -1.20%
    print(f"Market open: {is_market_open()}")
    print(f"Current IST: {current_ist()}")
