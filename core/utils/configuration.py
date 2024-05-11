import os
from typing import Union

from utils.db_config import db
from utils.enums import LoggerName


def _is_docker() -> bool:
    return os.environ.get("IS_DOCKER", "false").lower() == "true"


def get_config_value(key: str, default_value=None, include_secrets=True):
    search = {
        "$and": [
            {
                "$or": [
                    {"secret": {"$exists": False}},
                    {"secret": False}
                ]
            },
            {"_id": key}
        ]
    } if not include_secrets else {"_id": key}
    item = db["config"].find_one(search)
    if not item:
        return default_value
    return item


def set_config_value(item: dict, key: str = None, is_secret=False) -> bool:
    if not key:
        key = item.get("_id")
        if not key:
            return False
    if get_config_value(key):
        item["secret"] = is_secret
        db["config"].find_one_and_replace({"_id": key}, item)
        return True
    item["_id"] = key
    item["secret"] = is_secret
    db["config"].insert_one(item)
    return True


def get_log_location(logger_name: Union[str, LoggerName]):
    if isinstance(logger_name, LoggerName):
        logger_name = logger_name.value
    if _is_docker():
        return get_config_value(
            f"logs.docker.{logger_name}",
            default_value={"value": f"/logs/{logger_name}.log"}
        ).get("value")
    return get_config_value(
        f"logs.local.{logger_name}", default_value={"value": None}
    ).get("value")
