import os
import uuid

from flask import Blueprint, request

from api.house_base import House
from api.house_tracking import HouseAccess
from utils import validation, configuration
from utils.api_decorators import json_data, admin_required
from utils.db_config import db
from utils.validation import dict_types_valid

mod = Blueprint('api_fun_tools', __name__)


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
    for item in db["access"].find({}):
        if HouseAccess.visit_too_long(item):
            HouseAccess.evict(item["player_id"])
            evictions += 1
    return {"success": True, "evictions": evictions}


@mod.route("/api/trigger-evictions/all", methods=["POST"])
@admin_required
def trigger_all_evictions():
    items = db["access"].find({}, ["_id"])
    evictions: int = len([x for x in items])
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
    value = configuration.get_config_value(key)
    if not value:
        return {"success": False, "reason": "Key does not exist. Default value may be used."}
    return value


@mod.route("/api/config-dump")
@admin_required
def dump_config():
    values = [item for item in db["config"].find({})]
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

