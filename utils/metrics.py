import datetime
import os
import uuid
from typing import Optional

from prometheus_client import CollectorRegistry, push_to_gateway, Counter

from utils.db_config import db


class MetricTracker:

    def __init__(self):
        self.push_registry_host = os.environ.get("PUSH_REGISTRY")
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

    def get_registry(self):
        return self.registry

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
        db["metrics"].insert_one(db_entry)
        return self  # For syntax such as increment_http_request().push()

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
            push_to_gateway(self.push_registry_host, job='badge_server', registry=self.registry)
        except Exception:
            print(f"Failed to push metrics to {self.push_registry_host}!")


metric_tracker: Optional[MetricTracker] = None

