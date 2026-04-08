#!/usr/bin/env python3
# =============================================================
#  main.py — NiftyNinja Entry Point
#
#  This is the first file you run. It gives you a simple menu
#  to launch whichever part of the system you need.
#
#  Usage:  python main.py
# =============================================================

import subprocess
import sys
import os

# Make sure we can import from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_banner():
    print("""
  ╔═══════════════════════════════════════╗
  ║          🥷  NiftyNinja              ║
  ║   AI-Assisted Paper Trading System   ║
  ║          Indian Stock Market         ║
  ╚═══════════════════════════════════════╝
    """)


def menu():
    print("  What do you want to do?\n")
    print("  1.  Launch dashboard        (streamlit run dashboard/app.py)")
    print("  2.  Test data fetcher       (python data/fetcher.py)")
    print("  3.  Test signal engine      (python signals/engine.py)")
    print("  4.  Quick price check       (type a symbol, get current price)")
    print("  5.  Exit\n")
    return input("  Enter 1–5: ").strip()


def quick_price():
    """Fetch and display the current price of any NSE stock."""
    try:
        from data.fetcher import DataFetcher
        from utils.helpers import format_inr

        fetcher = DataFetcher()
        symbol  = input("  Enter NSE symbol (e.g. RELIANCE): ").strip().upper()

        if not symbol:
            print("  No symbol entered.")
            return

        print(f"\n  Fetching {symbol}...")
        quote = fetcher.get_quote(symbol)

        if quote.get("price", 0) == 0:
            print(f"  Could not fetch data for {symbol}. Check the symbol.")
            return

        price  = quote["price"]
        chg    = quote["change"]
        chg_pct = quote["change_pct"]
        arrow  = "▲" if chg >= 0 else "▼"

        print(f"\n  {symbol}")
        print(f"  Price:  {format_inr(price)}")
        print(f"  Change: {arrow} {format_inr(abs(chg))}  ({chg_pct:+.2f}%)")

    except ImportError as e:
        print(f"\n  Import error: {e}")
        print("  Have you activated your virtual environment?")
        print("  Run: source venv/bin/activate")


def main():
    print_banner()

    while True:
        choice = menu()

        if choice == "1":
            print("\n  Starting dashboard...")
            print("  Open http://localhost:8501 in your browser")
            print("  Press Ctrl+C to stop\n")
            try:
                subprocess.run(["streamlit", "run", "dashboard/app.py"])
            except KeyboardInterrupt:
                print("\n  Dashboard stopped.")
            except FileNotFoundError:
                print("\n  streamlit not found.")
                print("  Run: pip install streamlit")

        elif choice == "2":
            print("\n  Running data fetcher test...\n")
            subprocess.run([sys.executable, "data/fetcher.py"])

        elif choice == "3":
            print("\n  Running signal engine test...\n")
            subprocess.run([sys.executable, "signals/engine.py"])

        elif choice == "4":
            quick_price()

        elif choice == "5":
            print("\n  Bye!\n")
            break

        else:
            print("\n  Please enter 1, 2, 3, 4, or 5.\n")

        print()   # blank line between menu iterations


if __name__ == "__main__":
    main()
