import os
import uuid

from flask import Blueprint, request

from utils.api_decorators import json_data
from utils.db_config import db
from utils.validation import dict_types_valid

mod = Blueprint('api_fun_tools', __name__)


@mod.route("/api/reset-game", methods=["DELETE"])
def reset_game():
    reset_token = request.headers.get("X-API-Token", "")
    valid_token = os.environ.get("ADMINISTRATION_KEY", "default_token_hack_me_boi")
    if reset_token != valid_token:
        return {"success": False}, 401
    db["players"].delete_many({})
    db["houses"].delete_many({})
    return {"success": True}


@mod.route("/api/clear-registration", methods=["DELETE"])
def reset_registration():
    reset_token = request.headers.get("X-API-Token", "")
    valid_token = os.environ.get("ADMINISTRATION_KEY", "default_token_hack_me_boi")
    if reset_token != valid_token:
        return {"success": False}, 401
    db["registration"].delete_many({})
    default_item: dict = {
        "_id": str(uuid.uuid4()),
        "mac": "00:00:00:00:00:00",
        "notes": "Default Registration Value"
    }
    db["registration"].insert_one(default_item)
    return {"success": True, "registration": default_item}


@mod.route("/api/enable-registration", methods=["POST"])
def enable_registration():
    admin_token = request.headers.get("X-API-Token", "")
    valid_token = os.environ.get("ADMINISTRATION_KEY", "default_token_hack_me_boi")
    if admin_token != valid_token:
        return {"success": False}, 401
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
def disable_registration():
    admin_token = request.headers.get("X-API-Token", "")
    valid_token = os.environ.get("ADMINISTRATION_KEY", "default_token_hack_me_boi")
    if admin_token != valid_token:
        return {"success": False}, 401
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
    db["registration"].insert_one(data)
    return {"success": True, "message": data}

