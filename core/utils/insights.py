import datetime
import json
import uuid

from utils.db_config import db


def log_request(request, response):
    try:
        _log_request(request, response)
    except Exception:
        pass


def _log_request(request, response):
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
    request_method = request.method
    requester_ip = request.remote_addr
    http_path = request.url_rule.rule if request.url_rule else None
    now = datetime.datetime.now().isoformat()

    request_body = {}
    try:
        request_body = request.get_json()
    except Exception:
        pass

    db_entry = {
        "_id": str(uuid.uuid4()),
        "timestamp": now,
        "request": {
            "method": request_method,
            "endpoint": http_path,
            "ip": requester_ip,
            "player_id": player_id,
            "body": request_body
        },
        "response": {
            "status_code": status_code,
            "success": success,
            "body": response_json
        }
    }
    db["requests"].insert_one(db_entry)
