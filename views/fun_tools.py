import os

from flask import Blueprint, request

from utils.db_config import db

mod = Blueprint('api_fun_tools', __name__)


@mod.route("/reset-all", methods=["DELETE"])
def reset_all():
    reset_token = request.headers.get("X-API-Token", "")
    valid_token = os.environ.get("ADMINISTRATION_KEY", "default_token_hack_me_boi")
    if reset_token != valid_token:
        return {"success": False}, 401
    db["players"].delete_many({})
    db["houses"].delete_many({})
    return {"success": True}

