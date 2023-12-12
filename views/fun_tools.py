import os
import uuid

from flask import Blueprint, request

from utils.db_config import db

mod = Blueprint('api_fun_tools', __name__)


@mod.route("/reset-game", methods=["DELETE"])
def reset_game():
    reset_token = request.headers.get("X-API-Token", "")
    valid_token = os.environ.get("ADMINISTRATION_KEY", "default_token_hack_me_boi")
    if reset_token != valid_token:
        return {"success": False}, 401
    db["players"].delete_many({})
    db["houses"].delete_many({})
    return {"success": True}


@mod.route("/clear-registration", methods=["DELETE"])
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
