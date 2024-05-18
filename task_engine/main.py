import logging
import sys
import time

from utils import request_util

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ch = logging.StreamHandler(sys.stdout)
logger.addHandler(ch)


if __name__ == '__main__':
    logger.info("Launching...")
    while True:
        print("Running refresh_metrics()")
        try:
            request_util.refresh_metrics()
        except Exception:
            logger.error("Failed to refresh metrics")
        time.sleep(5)
