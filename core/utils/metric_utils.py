import datetime

from api.player_base import Player
from utils.db_config import db


def get_player_counts():
    # Threshold for player activity
    thirty_minutes_ago = (datetime.datetime.now() - datetime.timedelta(minutes=30)).isoformat()
    active_player_count = db["players"].count_documents({'last_activity': {'$gt': thirty_minutes_ago}})
    inactive_player_count = db["players"].count_documents({
        '$or': [
            {'last_activity': {'$lte': thirty_minutes_ago}},
            {'last_activity': {'$exists': False}},
        ]
    })
    return active_player_count, inactive_player_count


def get_house_counts():
    active_houses = db["houses"].count_documents({"abandoned": False})
    abandoned_houses = db["houses"].count_documents({"abandoned": True})
    return active_houses, abandoned_houses


def get_registration_counts():
    return db["registration"].count_documents({})


def get_players_in_houses():
    items = db["access"].find({}, ["player_id", "house_id"])
    in_own_house: int = 0
    in_other_house: int = 0
    for item in items:
        player_id: str = item["player_id"]  # Player inside some house
        house_id: str = item["house_id"]  # Which house the player is in.
        player_house_id = Player.get_player_house_id(player_id)
        if player_house_id == house_id:
            in_own_house += 1
        else:
            in_other_house += 1
    return in_own_house, in_other_house

