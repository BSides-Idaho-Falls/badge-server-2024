import json
import logging
import os
import uuid
from threading import Thread

from flask import Flask, request
from prometheus_client import generate_latest, REGISTRY

from utils import startup, metrics
from utils.db_config import db
from views import assets, api_house, api_player, renders, fun_tools, api_shop, api_game

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
if "PROMETHEUS_MULTIPROC_DIR" not in os.environ:
    os.environ["PROMETHEUS_MULTIPROC_DIR"] = "./metrics_configs/registry"

registers = [
    assets.mod,
    renders.mod,
    api_house.mod,
    api_player.mod,
    api_shop.mod,
    api_game.mod,
    fun_tools.mod
]

for registration in registers:
    app.register_blueprint(registration)


@app.errorhandler(404)
def page_not_found(e):
    return "404", 404


@app.errorhandler(500)
def server_error(e):
    return "500", 500


@app.route('/metrics')
def serve_metrics():
    metrics.refresh_metrics()
    return generate_latest(REGISTRY)


@app.after_request
def after_request(response):
    status_code = str(response.status_code)
    response_body = response.get_data(as_text=True)
    response_json: dict = {}
    player_id = "N/A"
    try:
        response_json = json.loads(response_body)
        if "player_id" in response_json:
            player_id = response_json["player_id"]
    except Exception:
        pass
    try:
        success = str(response_json.get("success", "N/A"))
    except Exception:
        success = "N/A"
    py_endpoint = request.endpoint
    request_method = request.method
    requester_ip = request.remote_addr
    http_path = request.url_rule.rule if request.url_rule else None

    metrics.metric_tracker.increment_http_request(
        method=request_method,
        endpoint=http_path,
        py_endpoint=py_endpoint,
        status=status_code,
        success=success,
        ip=requester_ip,
        player_id=player_id
    ).push()

    return response


startup.house_evictions()  # Clean up users who have been in a house too long.
metrics.metric_tracker = metrics.MetricTracker()

if __name__ == '__main__':
    host = "0.0.0.0"
    debug_mode = os.environ.get("DEBUG_MODE", "false").lower() == "true"
    app.run(debug=debug_mode, port=8080, host=host)
