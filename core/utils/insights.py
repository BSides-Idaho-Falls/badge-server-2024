import datetime
import json
import uuid

from utils.configuration import get_config_value
from utils.db_config import db


def log_request(request, response):
    try:
        _log_request(request, response)
    except Exception:
        pass


def sanitize_content(dict_item):
    if not get_config_value(
            "logs.sanitization", default_value={"value": True}
    ).get("value"):
        return dict_item

    fields = ["X-Api-Token", "token"]
    for field in fields:
        if field in dict_item:
            dict_item[field] = "<redacted>"

    return dict_item


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
    response_json = sanitize_content(response_json)
    request_method = request.method
    requester_ip = request.remote_addr
    http_path = request.url_rule.rule if request.url_rule else None
    now = datetime.datetime.now().isoformat()

    request_body = {}
    headers = {}

    try:
        request_body = sanitize_content(request.get_json())
    except Exception:
        pass
    try:
        headers = sanitize_content(dict(request.headers))
    except Exception:
        pass

    db_entry = {
        "_id": str(uuid.uuid4()),
        "timestamp": now,
        "request": {
            "method": request_method,
            "endpoint": http_path,
            "path": request.path,
            "ip": requester_ip,
            "player_id": player_id,
            "body": request_body,
            "headers": headers
        },
        "response": {
            "status_code": status_code,
            "success": success,
            "body": response_json
        }
    }
    db["requests"].insert_one(db_entry)
