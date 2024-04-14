import uuid
from typing import Union

from utils.db_config import db


def delete_player(player: Union[dict, str]):
    if isinstance(player, str):
        player = db["players"].find_one({"_id": player}, ["house_id"])
    player_id = player["_id"]
    if not player:
        return False, "Player doesn't exist"
    if house_id := player.get("house_id"):
        if house := db["houses"].find_one({"_id": house_id, "abandoned": False}):
            house["abandoned"] = True
            house["abandoned_by"] = player_id
            db["houses"].find_one_and_replace({"_id": house_id}, house)

    # new UUID so there's no overlaps. old ID can still be accessed via player_id
    player["_id"] = str(uuid.uuid4())
    db["deleted_players"].insert_one(player)
    db["players"].find_one_and_delete({"_id": player_id})
    return True, "success"
