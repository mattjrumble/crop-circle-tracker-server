from calendar import WEDNESDAY
from datetime import time

from pytz import timezone

LOCATIONS = {
    0: "Doric's House",
    1: "Yanille",
    2: "Draynor",
    3: "Rimmington",
    4: "Grand Exchange",
    5: "Farming Guild",
    6: "Hosidius",
    7: "Harmony Island",
    8: "Gwenith",
    9: "Catherby",
    10: "Tree Gnome Stronghold",
    11: "Brimhaven",
    12: "Mos Le'Harmless",
    13: "Taverley",
    14: "Lumbridge Mill",
    15: "East Ardougne",
    16: "South of Varrock",
    17: "Miscellania",
}

TIMEZONE = timezone('Europe/London')  # Use UK timezone to align with the weekly game update times
FIFTEEN_MINUTES = 15 * 60

DATABASE_FILENAME = 'db.sqlite3'

GAME_UPDATE_DAY = WEDNESDAY
GAME_UPDATE_TIME = time(hour=11, minute=30)
GAME_UPDATE_GRACE_PERIOD_SECONDS = 30 * 60

ESTIMATED_SERVER_LAG_RATE = (5 * 60) / (24 * 60 * 60)  # Assume up to 5 minutes of server lag every day
SERVER_LAG_LIMIT = FIFTEEN_MINUTES

API_KEY = 'gnomechild123'

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelname)s - %(asctime)s - %(message)s"
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelname)s - %(asctime)s - %(client_addr)s - "%(request_line)s" %(status_code)s',
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO"},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
    },
}
