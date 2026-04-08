# =============================================================
#  utils/logger.py
#  A simple logger that prints coloured output to terminal
#  and writes to a log file at the same time.
#
#  Usage (in any other file):
#      from utils.logger import get_logger
#      log = get_logger("MyModule")
#      log.info("Everything is fine")
#      log.warning("Something looks off")
#      log.error("Something broke")
# =============================================================

import logging
import os
from colorama import Fore, Style, init

# Makes colours work on Windows too
init(autoreset=True)


def get_logger(name: str) -> logging.Logger:
    """
    Create (or get existing) logger for a module.
    Each module passes its own name so log lines are easy to trace.
    Example: log = get_logger("DataFetcher")
    """
    from config import LOG_LEVEL, LOG_FILE

    # Make sure the logs directory exists
    os.makedirs("logs", exist_ok=True)

    logger = logging.getLogger(name)

    # Only add handlers once — prevents duplicate log lines
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # --- File handler (plain text, no colours) ---------------
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
    ))
    logger.addHandler(file_handler)

    # --- Console handler (coloured) --------------------------
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ColourFormatter())
    logger.addHandler(console_handler)

    return logger


class ColourFormatter(logging.Formatter):
    """Adds colour to log levels in the terminal."""

    COLOURS = {
        logging.DEBUG:    Fore.CYAN,
        logging.INFO:     Fore.GREEN,
        logging.WARNING:  Fore.YELLOW,
        logging.ERROR:    Fore.RED,
        logging.CRITICAL: Fore.MAGENTA,
    }

    def format(self, record):
        colour = self.COLOURS.get(record.levelno, "")
        message = super().format(record)
        return f"{colour}{message}{Style.RESET_ALL}"
