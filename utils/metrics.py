import datetime
import os
import uuid
from typing import Optional

from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter

from utils.db_config import db


class MetricTracker:

    def __init__(self):
        self.push_registry_host = os.environ.get("PUSH_REGISTRY", "localhost:9091")
        self.registry = CollectorRegistry()

        # Player_id and IP not included as it would be an unbounded label
        # and would cause storage to rise drastically with the expected amount
        # of HTTP requests
        self.http_request_counter = Counter(
            'http_requests_total',
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

        # Although player_id is unbounded, we don't expect a massive amount of changes.
        # This is generally *NOT* a good idea but hey. Let's stress test prometheus.
        # (Still not doing this with the http requests metrics)
        self.money_gauge = Gauge(
            "badgeserver_player_dollars",
            "How much money a player has",
            labelnames=[
                "player_id"
            ],
            registry=self.registry
        )

    def set_player_money(self, player_id: str, money: int):
        now = datetime.datetime.now().isoformat()
        self.money_gauge.labels(
            player_id=player_id
        ).set(money)
        db_entry = {
            "_id": str(uuid.uuid4()),
            "timestamp": now,
            "metric": "badgeserver_player_dollars",
            "metric_type": "gauge",
            "labels": {
                "player_id": player_id
            },
            "value": {
                "set": money
            }
        }
        db["metrics"].insert_one(db_entry)
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
            "metric": "http_requests_total",
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
        db["metrics"].insert_one(db_entry)
        return self  # For syntax such as increment_http_request().push()

    def push(self):
        try:
            push_to_gateway(self.push_registry_host, job='badge_server', registry=self.registry)
        except Exception:
            print(f"Failed to push metrics to {self.push_registry_host}!")


metric_tracker: Optional[MetricTracker] = None

