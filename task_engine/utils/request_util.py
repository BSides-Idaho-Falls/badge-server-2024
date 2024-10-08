import logging
import os
import sys

import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ch = logging.StreamHandler(sys.stdout)
logger.addHandler(ch)


def _get_base_path():
    host_name = os.environ.get("API_IP")
    return f"http://{host_name}:8080" if host_name else None


def refresh_metrics():
    if base_path := _get_base_path():
        response = requests.get(f"{base_path}/refresh-metrics")
        logger.info(response.text)
    else:
        logger.error("No logging base path")


def trigger_evictions():
    headers = {
        "X-API-Token": os.environ.get("API_KEY", "")
    }
    if base_path := _get_base_path():
        response = requests.post(f"{base_path}/api/trigger-evictions", headers=headers)
        logger.info(response.text)
    else:
        logger.error("No logging base path")
