import logging
import os
import sys
from logging import handlers

from api.house_tracking import HouseAccess
from utils.configuration import get_config_value, get_log_location
from utils.db_config import db
from utils.enums import LoggerName

MAX_BYTES = get_config_value(
    "logs.rotation.max_bytes", {"value": (10 * (1000 * 1000))}
).get("value")
logger = logging.getLogger(LoggerName.SYSTEM.value)
logger.setLevel(logging.INFO)
log_location = get_log_location(LoggerName.SYSTEM)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(formatter)
logger.addHandler(ch)

if log_location:
    handler = handlers.RotatingFileHandler(log_location, maxBytes=MAX_BYTES, backupCount=10)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def house_evictions():
    evictions: int = 0
    for item in db["access"].find({}):
        if HouseAccess.visit_too_long(item):
            HouseAccess.evict(item["player_id"])
            evictions += 1
    logger.info(f"Evicted {evictions} people from houses!")


def warnings():
    if not os.environ.get("GRAVWELL_HOST"):
        logger.warning("No GRAVWELL_HOST defined, no logs will be exported to gravwell")

