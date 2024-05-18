import datetime
import json
import os
import socket
import uuid
from _socket import gaierror
from typing import Union

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


def _send_data(data: Union[list, str]):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = os.environ.get("GRAVWELL_HOST")
    try:
        port = int(os.environ.get("GRAVWELL_PORT", 7778))
    except Exception:
        #logger.warning("Unable to parse GRAVWELL_PORT and so no metrics exported")
        return
    if not host:
        return
    if isinstance(data, dict):
        data = json.dumps(data)
    if isinstance(data, str):
        data = [data]
    try:
        client_socket.connect((host, port))
        for line in data:
            client_socket.sendall(line.encode())
            client_socket.sendall(b'\n')

        client_socket.close()
    except gaierror:
        pass
        #logger.warning(f"Gravwell not accessible, offline? {host}:{port}")
    except Exception as e:
        pass
        #logger.error("Error:", e)


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
    _send_data(db_entry)
