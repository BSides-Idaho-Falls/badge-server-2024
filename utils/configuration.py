from utils.db_config import db


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


def set_config_value(item: dict, key: str = None) -> bool:
    if not key:
        key = item.get("_id")
        if not key:
            return False
    if get_config_value(key):
        db["config"].find_one_and_replace({"_id": key}, item)
        return True
    item["_id"] = key
    db["config"].insert_one(item)
    return True
