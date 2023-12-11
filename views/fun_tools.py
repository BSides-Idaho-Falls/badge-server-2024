from flask import Blueprint

from utils.db_config import db

mod = Blueprint('api_fun_tools', __name__)


@mod.route("/reset-all", methods=["DELETE"])
def reset_all():
    db["players"].delete_many({})
    db["houses"].delete_many({})
    return {"success": True}

