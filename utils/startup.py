from api.house_tracking import HouseAccess
from utils.db_config import db


def house_evictions():
    evictions: int = 0
    for item in db["access"].find({}):
        if HouseAccess.visit_too_long(item):
            HouseAccess.evict(item["player_id"])
            evictions += 1
    print(f"Evicted {evictions} people from houses!")
