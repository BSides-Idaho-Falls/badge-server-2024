import datetime
import json
import logging
import os
import socket
import sys
import threading
import uuid
from _socket import gaierror
from logging import handlers
from typing import Union

from prometheus_client import push_to_gateway, Counter, Gauge, CollectorRegistry

from utils import metric_utils
from utils.configuration import get_log_location, get_config_value
from utils.db_config import db
from utils.enums import LoggerName

MAX_BYTES = get_config_value(
    "logs.rotation.max_bytes", {"value": (10 * (1000 * 1000))}
).get("value")
logger = logging.getLogger(LoggerName.METRICS.value)
logger.setLevel(logging.INFO)
log_location = get_log_location(LoggerName.METRICS)

ch = logging.StreamHandler(sys.stdout)
logger.addHandler(ch)

if log_location:
    handler = handlers.RotatingFileHandler(log_location, maxBytes=MAX_BYTES, backupCount=10)
    logger.addHandler(handler)


class MetricTracker:

    def __init__(self):
        self.push_registry_host = os.environ.get("PUSH_REGISTRY")
        print(f"Push registry host: {self.push_registry_host}")
        self.registry = CollectorRegistry()

        # Player_id and IP not included as it would be an unbounded label
        # and would cause storage to rise drastically with the expected amount
        # of HTTP requests
        self.http_request_counter = Counter(
            'apiserver_http_requests_total',
            'HTTP Request Counter',
            labelnames=[
                "method",
                "endpoint",
                "py_endpoint",
                "status",
                "success"
            ],
            registry=self.registry
        )

        self.robberies_counter = Counter(
            "apiserver_robberies_total",
            "Count of robberies",
            labelnames=[
                "successful"
            ],
            registry=self.registry
        )

        self.robberies_gauge = Gauge(
            "apiserver_robbery_attempts",
            "Number of robbery attempts",
            labelnames=[
                "successful"
            ],
            registry=self.registry
        )

        self.players = Gauge(
            "apiserver_players_number",
            "Number of players",
            labelnames=[
                "active"
            ],
            registry=self.registry
        )

        self.houses = Gauge(
            "apiserver_houses_number",
            "Number of houses",
            labelnames=[
                "abandoned"
            ],
            registry=self.registry
        )

        self.registration = Gauge(
            "apiserver_registration_tokens",
            "Number of registration tokens",
            registry=self.registry
        )

        self.houses_occupied = Gauge(
            "apiserver_houses_occupied_players",
            "Number of players inside houses",
            labelnames=[
                "houseowner"
            ],
            registry=self.registry
        )

    def _send_data(self, data: Union[list, str]):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = os.environ.get("GRAVWELL_HOST")
        try:
            port = int(os.environ.get("GRAVWELL_PORT", 7777))
        except Exception:
            logger.warning("Unable to parse GRAVWELL_PORT and so no metrics exported")
            return
        if not host:
            logger.warning("GRAVWELL_HOST not configured!")
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
            logger.warning(f"Gravwell not accessible, offline? {host}:{port}")
        except Exception as e:
            logger.error("Error:", e)

    def write_entry(self, entry):
        """Allow writing metric entry to multiple locations such as DB & file."""
        db["metrics"].insert_one(entry)
        logger.info(entry)
        self._send_data(entry)

    def increment_robbery_attempt(self, successful: Union[bool, str]):
        self.robberies_gauge.labels(successful=str(successful)).inc(1)
        self.robberies_counter.labels(successful=str(successful)).inc(1)
        now = datetime.datetime.now()
        db_entry = {
            "_id": str(uuid.uuid4()),
            "timestamp": now,
            "metric": "apiserver_robbery_attempts",
            "metric_type": "Gauge",
            "labels": {
                "successful": str(successful)
            },
            "value": {
                "inc": 1
            }
        }
        self.write_entry(db_entry)
        db_entry["metric"] = "apiserver_robberies_total"
        db_entry["metric_type"] = "counter"
        self.write_entry(db_entry)
        return self

    def set_players(self, number, active: Union[bool, str]):
        self.players.labels(
            active=str(active)
        ).set(number)
        now = datetime.datetime.now().isoformat()
        db_entry = {
            "_id": str(uuid.uuid4()),
            "timestamp": now,
            "metric": "apiserver_players_number",
            "metric_type": "Gauge",
            "labels": {
                "active": str(active)
            },
            "value": {
                "set": number
            }
        }
        self.write_entry(db_entry)
        return self

    def set_house_occupied(self, number, houseowner: Union[bool, str]):
        self.houses_occupied.labels(
            houseowner=str(houseowner)
        ).set(number)
        now = datetime.datetime.now().isoformat()
        db_entry = {
            "_id": str(uuid.uuid4()),
            "timestamp": now,
            "metric": "apiserver_houses_occupied_players",
            "metric_type": "Gauge",
            "labels": {
                "houseowner": str(houseowner)
            },
            "value": {
                "set": number
            }
        }
        self.write_entry(db_entry)
        return self

    def set_registration_tokens(self, number):
        self.registration.set(number)
        now = datetime.datetime.now().isoformat()
        db_entry = {
            "_id": str(uuid.uuid4()),
            "timestamp": now,
            "metric": "apiserver_registration_tokens",
            "metric_type": "Gauge",
            "labels": {},
            "value": {
                "set": number
            }
        }
        self.write_entry(db_entry)
        return self

    def set_houses(self, number, abandoned: Union[bool, str]):
        self.houses.labels(
            abandoned=str(abandoned)
        ).set(number)
        now = datetime.datetime.now().isoformat()
        db_entry = {
            "_id": str(uuid.uuid4()),
            "timestamp": now,
            "metric": "apiserver_houses_number",
            "metric_type": "Gauge",
            "labels": {
                "abandoned": str(abandoned)
            },
            "value": {
                "set": number
            }
        }
        self.write_entry(db_entry)
        return self

    def increment_http_request(self, method, endpoint, py_endpoint, status, success, ip=None, player_id=None):
        if not ip:
            ip = "N/A"
        if not player_id:
            player_id = "N/A"
        self.http_request_counter.labels(
            method=method,
            endpoint=endpoint,
            py_endpoint=py_endpoint,
            status=status,
            success=success
        ).inc(1)
        now = datetime.datetime.now().isoformat()
        db_entry = {
            "_id": str(uuid.uuid4()),
            "timestamp": now,
            "metric": "apiserver_http_requests_total",
            "metric_type": "counter",
            "labels": {
                "method": method,
                "endpoint": endpoint,
                "status": status,
                "success": success,
                "ip": ip,
                "player_id": player_id
            },
            "value": {
                "inc": 1
            }
        }
        self.write_entry(db_entry)
        return self

    def push(self):
        """
        Not necessary for /metrics, but necessary if you have a prometheus
        push gateway.

        Warning: not all metrics will get published to the push registry unless
        /metrics is called on this server.
        """
        if not self.push_registry_host:
            return
        try:
            job_name = f"t_{threading.get_native_id()}"
            push_to_gateway(self.push_registry_host, job=job_name, registry=self.registry)
        except Exception:
            print(f"Failed to push metrics to {self.push_registry_host}!")


metric_tracker = MetricTracker()


def refresh_metrics(metric_tracker):

    # Count active and inactive players
    active_player_count, inactive_player_count = metric_utils.get_player_counts()
    metric_tracker.set_players(active_player_count, True).push()
    metric_tracker.set_players(inactive_player_count, False).push()

    # Count houses and abandoned houses
    active_houses, abandoned_houses = metric_utils.get_house_counts()
    metric_tracker.set_houses(active_houses, False).push()
    metric_tracker.set_houses(abandoned_houses, True).push()

    # Count registration tokens
    metric_tracker.set_registration_tokens(metric_utils.get_registration_counts()).push()

    # Count players in houses (active robberies)
    in_own_house, in_other_house = metric_utils.get_players_in_houses()
    metric_tracker.set_house_occupied(in_own_house, True).push()
    metric_tracker.set_house_occupied(in_other_house, False).push()


