import logging
import os
import uuid

from flask import Flask

from utils.db_config import db
from views import assets, api_house, api_player, renders, fun_tools, api_shop

logger = logging.getLogger('System')


def get_secret_key():
    logger.info("Grabbing the secret sauce.")
    flask_key = db["config"].find_one({"_id": "flask_key"})
    if not flask_key:
        key = str(uuid.uuid4())
        db["config"].insert_one({
            "_id": "flask_key",
            "key": key
        })
        return key
    return flask_key["key"]


app = Flask(__name__)
app.secret_key = get_secret_key()

registers = [
    assets.mod,
    renders.mod,
    api_house.mod,
    api_player.mod,
    api_shop.mod,
    fun_tools.mod
]

for registration in registers:
    app.register_blueprint(registration)


@app.errorhandler(404)
def page_not_found(e):
    return "404"


if __name__ == '__main__':
    host = "0.0.0.0"
    debug_mode = os.environ.get("DEBUG_MODE", "false").lower() == "true"
    app.run(debug=debug_mode, port=8080, host=host)
