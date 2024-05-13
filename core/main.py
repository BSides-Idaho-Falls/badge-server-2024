import json
import logging
import os
import uuid

from flask import Flask, request

from utils import startup, metrics
from utils.db_config import db
from utils.insights import log_request
from views import assets, api_house, api_player, renders, administration, api_shop, api_game


def get_secret_key():
    flask_key = db["config"].find_one({"_id": "flask_key"})
    if not flask_key:
        key = str(uuid.uuid4())
        db["config"].insert_one({
            "_id": "flask_key",
            "key": key,
            "secret": True
        })
        return key
    if "secret" not in flask_key:
        flask_key["secret"] = True
        db["config"].find_one_and_replace({"_id": "flask_key"}, flask_key)
    return flask_key["key"]


def create_app():
    app = Flask(__name__)
    app.secret_key = get_secret_key()
    app.logger.setLevel(logging.INFO)
    if "PROMETHEUS_MULTIPROC_DIR" not in os.environ:
        os.environ["PROMETHEUS_MULTIPROC_DIR"] = "./metrics_configs/registry"

    registers = [
        assets.mod,
        renders.mod,
        api_house.mod,
        api_player.mod,
        api_shop.mod,
        api_game.mod,
        administration.mod
    ]

    for registration in registers:
        app.register_blueprint(registration)

    with app.app_context():
        app.metric_tracker = metrics.metric_tracker

    @app.errorhandler(404)
    def page_not_found(e):
        return "404", 404

    @app.errorhandler(500)
    def server_error(e):
        return "500", 500

    @app.route('/refresh-metrics')
    def serve_metrics():
        """Refresh / recalculate metrics data."""
        with app.app_context():
            metrics.refresh_metrics(app.metric_tracker)
            # Very buggy with gunicorn workers. Using push-registry / gravwell instead.
            # return generate_latest(app.metric_tracker.registry)
            return {"success": True}

    @app.after_request
    def after_request(response):
        status_code = str(response.status_code)
        response_body = None
        if not request.endpoint.startswith("asset."):
            response_body = response.get_data(as_text=True)
        response_json: dict = {}
        player_id = "N/A"
        try:
            response_json = json.loads(response_body) if response_body else None
            if response_json and "player_id" in response_json:
                player_id = response_json["player_id"]
        except Exception:
            pass
        try:
            success = str(response_json.get("success", "N/A")) if response_json else False
        except Exception:
            success = "N/A"
        py_endpoint = request.endpoint
        request_method = request.method
        requester_ip = request.remote_addr
        http_path = request.url_rule.rule if request.url_rule else None
        log_request(request, response)
        with app.app_context():
            app.metric_tracker.increment_http_request(
                method=request_method,
                endpoint=http_path,
                py_endpoint=py_endpoint,
                status=status_code,
                success=success,
                ip=requester_ip,
                player_id=player_id
            ).push()
            return response

    return app


startup.house_evictions()  # Clean up users who have been in a house too long.
startup.warnings()

app = create_app()

if __name__ == '__main__':
    host = "0.0.0.0"
    debug_mode = os.environ.get("DEBUG_MODE", "false").lower() == "true"
    app.run(debug=debug_mode, port=8080, host=host)
