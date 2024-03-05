import datetime
import os
import uuid
from typing import Optional, Union

from prometheus_client import push_to_gateway, Counter, Gauge, REGISTRY

from utils import metric_utils
from utils.db_config import db


class MetricTracker:

    def __init__(self):
        self.push_registry_host = os.environ.get("PUSH_REGISTRY")
        print(f"Push registry host: {self.push_registry_host}")
        #self.registry = CollectorRegistry()

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
            ]
        )

        self.robberies_counter = Counter(
            "apiserver_robberies_total",
            "Count of robberies",
            labelnames=[
                "successful"
            ]
        )

        self.robberies_gauge = Gauge(
            "apiserver_robbery_attempts",
            "Number of robbery attempts",
            labelnames=[
                "successful"
            ]
        )

        self.players = Gauge(
            "apiserver_players_number",
            "Number of players",
            labelnames=[
                "active"
            ]
        )

        self.houses = Gauge(
            "apiserver_houses_number",
            "Number of houses",
            labelnames=[
                "abandoned"
            ]
        )

        self.registration = Gauge(
            "apiserver_registration_tokens",
            "Number of registration tokens"
        )

        self.houses_occupied = Gauge(
            "apiserver_houses_occupied_players",
            "Number of players inside houses",
            labelnames=[
                "houseowner"
            ]
        )

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
        db["metrics"].insert_one(db_entry)
        db_entry["metric"] = "apiserver_robberies_total"
        db_entry["metric_type"] = "counter"
        db["metrics"].insert_one(db_entry)
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
        db["metrics"].insert_one(db_entry)
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
        db["metrics"].insert_one(db_entry)
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
        db["metrics"].insert_one(db_entry)
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
            push_to_gateway(self.push_registry_host, job='badge_server', registry=REGISTRY)
        except Exception:
            print(f"Failed to push metrics to {self.push_registry_host}!")


metric_tracker: Optional[MetricTracker] = None


def refresh_metrics():

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


