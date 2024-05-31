import datetime

from flask import Blueprint

from api.house_base import House
from api.house_tracking import HouseAccess
from utils import validation, configuration, player_utils
from utils.api_decorators import json_data, admin_required
from utils.db_config import db
from utils.validation import dict_types_valid

mod = Blueprint('api_fun_tools', __name__)


def determine_purge_remaining(players, options: dict):
    # How many players will remain for the registration key after the purge?
    # The player to keep will be based on either who has the most money, or who was created first.
    remaining_players: int = options.get("remaining_players", 1)
    delete_by: str = options.get("delete_by", "money")  # all | money | first_created
    if delete_by == "all":
        return []
    elif delete_by == "money":
        house_ids: list = [{"house_id": p.get("house_id")} for p in players]
        houses: list = []
        if len(house_ids) == 1:
            house = db["houses"].find_one({"house_id"}, ["_id", "house_id", "vault_contents"])
            if house:
                houses.append(house)
        else:
            houses = [house for house in db["houses"].find(
                {
                    "$or": house_ids
                },
                ["_id", "house_id", "vault_contents"]
            )]
        money_mapping: dict = {}
        for house in houses:
            vault_contents: dict = house.get("vault_contents", {})
            dollars: int = vault_contents.get("dollars", 0)
            money_mapping[house.get("house_id")] = dollars
        for p in players:
            p["dollars"] = money_mapping[p["house_id"]]
        sorted_players = sorted(players, key=lambda d: d['dollars'], reverse=True)
        keepers: list = []
        for i in range(0, remaining_players):
            if len(sorted_players) < 1:
                return keepers
            keepers.append(sorted_players.pop(0))
        return keepers
    elif delete_by == "first_created":
        keepers: list = []
        future = (datetime.datetime.now() + datetime.timedelta(minutes=1)).isoformat()
        sorted_players = sorted(players, key=lambda d: d.get("first_created", future))
        for i in range(0, remaining_players):
            if len(sorted_players) < 1:
                return keepers
            keepers.append(sorted_players.pop(0))
        return keepers
    raise NotImplementedError("Invalid option")


@mod.route("/api/purge-players", methods=["POST"])
@admin_required
@json_data
def purge_players(data):
    """
    Purge excess players based on a registration key.
    :param data:
    {
      "registration_key": "str - Registration key",
      "options": {  # Additional options
        "remaining_players": 1,  # How many players will remain for the key after the purge.
        "delete_by": "money | first_created | all"  # Delete by most money, or first created
      }
    }
    :return:
    """
    registration_key: str = data.get("registration_key")
    if not registration_key:
        return {"success": False, "reason": "No registration key provided"}
    options: dict = data.get("options", {})
    players = [p for p in db["players"].find(
        {"registered_by": registration_key},
        ["_id", "player_id", "house_id", "first_created"]
    )]
    deleted = 0
    try:
        keepers: list = determine_purge_remaining(players, options)
        keeper_ids = [k["_id"] for k in keepers]
        print(players)
        print(keepers)
        for player in players:
            if player["_id"] in keeper_ids:
                continue
            player_utils.delete_player(player)
            deleted += 1
    except NotImplementedError as e:
        return {"success": False, "reason": "Invalid options."}, 400
    return {"success": True, "deleted": deleted}


@mod.route("/api/delete-player/<player_id>", methods=["DELETE"])
@admin_required
def delete_player(player_id):
    success, message = player_utils.delete_player(player_id)
    if not success:
        return {"success": False, "reason": message}
    return {"success": True}


@mod.route("/api/reset-game", methods=["DELETE"])
@admin_required
def reset_game():
    db["players"].delete_many({})
    db["houses"].delete_many({})
    db["access"].delete_one({})
    return {"success": True}


@mod.route("/api/clear-registration", methods=["DELETE"])
@admin_required
def reset_registration():
    db["registration"].delete_many({})
    default_item: dict = {
        "_id": validation.generate_luhn(16),
        "mac": "00:00:00:00:00:00",
        "notes": "Default Registration Value"
    }
    db["registration"].insert_one(default_item)
    return {"success": True, "registration": default_item}


@mod.route("/api/enable-registration", methods=["POST"])
@admin_required
def enable_registration():
    config_item = db["config"].find_one({"_id": "self-registration"})
    if not config_item:
        db["config"].insert_one({
            "_id": "self-registration",
            "enabled": True
        })
        return {"success": True}
    config_item["enabled"] = True
    db["config"].find_one_and_replace({"_id": "self-registration"}, config_item)
    return {"success": True}


@mod.route("/api/disable-registration", methods=["POST"])
@admin_required
def disable_registration():
    config_item = db["config"].find_one({"_id": "self-registration"})
    if not config_item:
        db["config"].insert_one({
            "_id": "self-registration",
            "enabled": False
        })
        return {"success": True}
    config_item["enabled"] = False
    db["config"].find_one_and_replace({"_id": "self-registration"}, config_item)
    return {"success": True}


@mod.route("/api/trigger-evictions", methods=["POST"])
@admin_required
def trigger_evictions():
    evictions: int = 0
    for item in db["access"].find({}, ["_id", "player_id"]):
        if HouseAccess.visit_too_long(item):
            HouseAccess.evict(item["player_id"])
            evictions += 1
    return {"success": True, "evictions": evictions}


@mod.route("/api/trigger-evictions/all", methods=["POST"])
@admin_required
def trigger_all_evictions():
    items = db["access"].find({}, ["_id", "player_id"])
    evictions: int = len([x for x in items])
    failed_evictions: int = 0
    for item in items:
        success = HouseAccess.evict(item["player_id"]).get("success", False)
        if not success:
            failed_evictions += 1

    return {"success": True, "evictions": evictions}


@mod.route("/api/config/<key>", methods=["POST"])
@admin_required
@json_data
def set_config(key, data):
    configuration.set_config_value(data, key)
    return {"success": True}


@mod.route("/api/config/<key>", methods=["GET"])
@admin_required
def get_config(key):
    value = configuration.get_config_value(key, include_secrets=False)
    if not value:
        return {"success": False, "reason": "Key does not exist."}
    return value


@mod.route("/api/config-dump")
@admin_required
def dump_config():
    values = [item for item in db["config"].find({
        "$or": [
            {"secret": {"$exists": False}},
            {"secret": False}
        ]
    })]
    return {"success": True, "count": len(values), "items": values}


@mod.route("/api/self-register", methods=["POST"])
@json_data
def self_registration(data):
    config_item = db["config"].find_one({"_id": "self-registration"})
    if not config_item or not config_item.get("enabled", False):
        return {"success": False, "reason": "self registration disabled."}, 400
    if not dict_types_valid(data, {
        "_id": {
            "type": str,
            "required": True
        },
        "mac": {
            "type": str,
            "required": True
        }
    }):
        return {"success": False, "reason": "Malformed Data"}, 400
    data["notes"] = "Self registered badge"
    item = db["registration"].find_one({"mac": data["mac"]})
    if item:
        return {
            "success": False,
            "reason": "This mac address has already been registered.",
            "register_token": item["_id"]  # Returned because this is to help with automated self registration.
        }
    item = db["registration"].find_one({"_id": data["_id"]})
    if item:
        return {
            "success": False,
            "reason": "duplicate key found."
        }
    token_valid = validation.check_luhn(data["_id"])
    if not token_valid:
        print("Self registration failed (Failed luhn test)")
        return {
            "success": False,
            "reason": "Self generated token is not valid."
        }
    db["registration"].insert_one(data)
    return {"success": True, "message": data}


@mod.route("/api/test/bytes")
def get_some_bytes():
    byte_list = b'\x05' * 16
    bites = bytes(byte_list)
    response_data = {'bytes': bites.decode('latin-1'), 'additional_data': "x"}
    return response_data


@mod.route("/api/test/compare/<house_id1>/<house_id2>")
def compare_houses(house_id1, house_id2):
    house1: House = House(house_id=house_id1).load()
    house2: House = House(house_id=house_id2).load()

    if not house1 or not house2:
        return {"success": False, "reason": "One or more houses doesn't exist"}

    return {
        "success": True,
        "house1": house1.vault_contents.dollars,
        "house2": house2.vault_contents.dollars
    }
