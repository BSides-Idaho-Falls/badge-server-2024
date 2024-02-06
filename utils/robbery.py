import random
from typing import Optional, List

from utils.db_config import db


def find_unoccupied_house(exclusions: Optional[List[str]] = None) -> str:
    if not exclusions:
        exclusions = []
    houses = db["houses"].find({
        "abandoned": False
    }, ["house_id"])
    accesses: List[str] = [item["house_id"] for item in db["access"].find({}, ["house_id"])]
    open_houses: List[str] = []
    for house in houses:
        house_id: str = house["house_id"]
        if house_id in open_houses:
            continue
        if house_id not in accesses and house_id not in exclusions:
            open_houses.append(house_id)
    return random.choice(open_houses) if len(open_houses) > 0 else None



