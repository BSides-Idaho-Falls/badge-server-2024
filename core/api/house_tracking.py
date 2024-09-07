import datetime
import json
import logging
import sys
from logging import handlers
from typing import Optional, List, Union

from api.house_base import House
from api.material_base import Material
from api.materials import Air
from utils import metrics
from utils.configuration import get_config_value, get_log_location
from utils.db_config import db
from utils.enums import LoggerName

MAX_BYTES = get_config_value(
    "logs.rotation.max_bytes", {"value": (10 * (1000 * 1000))}
).get("value")
logger = logging.getLogger(LoggerName.SYSTEM.value)
logger.setLevel(logging.INFO)
log_location = get_log_location(LoggerName.SYSTEM)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(formatter)
logger.addHandler(ch)

if log_location:
    handler = handlers.RotatingFileHandler(log_location, maxBytes=MAX_BYTES, backupCount=10)
    handler.setFormatter(formatter)
    logger.addHandler(handler)



class HouseAccess:

    def __init__(self, player_id: str, house_id: str):
        self.player_id = player_id  # Player inside of house (Not house's owner)
        self.house_id = house_id  # House player is inside of
        self.house: Optional[House] = None
        self.player_location: Optional[List[int]] = None

    def load(self):
        self.house: House = House(house_id=self.house_id).load()
        db_access = db["access"].find_one({
            "player_id": self.player_id
        })
        if db_access:
            self.player_location = db_access["player_location"]
        return self if self.house else None

    def get_players_house_id(self):
        item = db["players"].find_one({"player_id": self.player_id}, ["house_id"])
        if not item:
            return None
        return item.get("house_id")

    def player_owns_house(self):
        house_id_compare = self.get_players_house_id()
        return house_id_compare and house_id_compare == self.house_id

    def is_in_house(self):
        db_access = db["access"].find_one({
            "player_id": self.player_id
        })
        return True if db_access else False

    def can_enter_house(self):
        db_access = db["access"].find_one({
            "house_id": self.house_id
        })
        if not db_access:
            return True
        visit_too_long = HouseAccess.visit_too_long(db_access)
        if visit_too_long:
            HouseAccess.evict(db_access["player_id"])
            return True
        return False

    def render_surroundings(self, player_location: Optional[List[int]] = None, compressed_view: bool = False) -> dict:
        absolute_player_location: Optional[List[int]] = player_location or self.player_location
        if not absolute_player_location:
            return {}
        player_local_location: List[int] = [3, 3]

        remote_x = absolute_player_location[0] - player_local_location[0]
        remote_y = absolute_player_location[1] - player_local_location[1]

        compressed_render = self.get_compressed_render(remote_x, remote_y, player_local_location)
        explicit_render = self.get_explicit_render(remote_x, remote_y, player_local_location)

        wood_walls: int = self.house.vault_contents.materials.get("Wooden_Wall", 0)

        c_size = len(json.dumps(compressed_render))
        e_size = len(json.dumps(explicit_render))
        resources = {
            "wood_walls": wood_walls
        }
        if compressed_view:
            if c_size > e_size:
                logger.info(
                    f"Explicit render is smaller than the compressed! "
                    f"Returning this instead. {c_size} > {e_size}"
                )
                return {**explicit_render, **resources}
            return {**compressed_render, **resources}
        return {**explicit_render, **resources}

    def get_explicit_render(self, remote_x, remote_y, player_local_location):
        local_x: int = 0
        construction: List[Union[dict, str]] = []
        for x in range(remote_x, remote_x + 8):
            local_y: int = 0
            for y in range(remote_y, remote_y + 8):
                if local_x == player_local_location[0] and local_y == player_local_location[1]:
                    construction.append({
                        "material_type": "player",
                        "local_location": [local_x, local_y],
                        "absolute_location": [x, y],
                        "passable": False
                    })
                    local_y += 1
                    continue
                material: Optional[Material] = self.house.get_material_from(x, y)
                if not material:
                    # Out of Bounds
                    construction.append({
                        "material_type": "House_Wall",
                        "local_location": [local_x, local_y],
                        "absolute_location": [x, y],
                        "passable": False
                    })
                    local_y += 1
                    continue
                passable = material.material_type.value == "Air"  # TODO figure out passable
                if not passable and x == 0 and y == 15:  # Door
                    passable = True
                if material.material_type.value != "Air":
                    construction.append({
                        "material_type": material.material_type.value.replace(" ", "_"),
                        "local_location": [local_x, local_y],
                        "absolute_location": [x, y],
                        "passable": passable
                    })
                local_y += 1
            local_x += 1
        return {"construction": construction}

    def get_compressed_render(self, remote_x, remote_y, player_local_location):
        # TODO: Make even smaller w/ bytes
        construction: List[str] = []
        local_x: int = 0
        for x in range(remote_x, remote_x + 8):
            local_y: int = 0
            for y in range(remote_y, remote_y + 8):
                if local_x == player_local_location[0] and local_y == player_local_location[1]:
                    construction.append("p")
                    local_y += 1
                    continue
                material: Optional[Material] = self.house.get_material_from(x, y)
                if not material:
                    # Out of Bounds
                    value = "1"
                    if x == 0 and y == 15:
                        value = "d"
                    construction.append(value)
                    local_y += 1
                    continue
                if material.material_type.value != "Air":
                    if material.material_type.value == "Vault":
                        construction.append("v")
                    else:
                        value = "1"
                        if x == 0 and y == 15:
                            value = "d"
                        construction.append(value)
                else:
                    value = "0"
                    if x == 0 and y == 15:
                        value = "d"
                    construction.append(value)
                local_y += 1
            local_x += 1
        return {"construction": "".join(construction)}

    def move(self, direction, compressed_view=False):
        direction = direction.lower()
        if direction not in ["left", "right", "up", "down"]:
            return None
        if direction == "left":
            return self.move_left(compressed_view=compressed_view)
        if direction == "right":
            return self.move_right(compressed_view=compressed_view)
        if direction == "up":
            return self.move_up(compressed_view=compressed_view)
        return self.move_down(compressed_view=compressed_view)  # Should always be down because of string whitelist.

    def move_up(self, compressed_view=False):
        return self._teleport_to(
            self.player_location[0], self.player_location[1] + 1,
            compressed_view=compressed_view
        )

    def move_down(self, compressed_view=False):
        return self._teleport_to(
            self.player_location[0], self.player_location[1] - 1,
            compressed_view=compressed_view
        )

    def move_left(self, compressed_view=False):
        return self._teleport_to(
            self.player_location[0] - 1, self.player_location[1],
            compressed_view=compressed_view
        )

    def move_right(self, compressed_view=False):
        return self._teleport_to(
            self.player_location[0] + 1, self.player_location[1],
            compressed_view=compressed_view
        )

    def rob_vault(self):
        if self.player_owns_house():
            return  # Can't rob your own house!
        logger.info(f"{self.player_id} is robbing vault of {self.house_id}")
        house: House = House(self.house_id).load()
        robbers_house_id = self.get_players_house_id()
        if not robbers_house_id:
            return
        robbers_house: House = House(house_id=robbers_house_id).load()
        dollars: int = house.vault_contents.dollars

        robbers_house.vault_contents.increase_dollars(dollars)
        house.vault_contents.dollars = 0

        house.save()
        robbers_house.save()
        metrics.metric_tracker.increment_robbery_attempt(True)

        return {"success": True, "robbed": True, "contents": {"dollars": dollars}}

    def _teleport_to(self, x: int, y: int, compressed_view=False):
        if not self.is_in_house():
            return None
        material: Optional[Material] = self.house.get_material_from(x, y)
        if not material:
            if not (x == 0 and y == 15):  # Door location
                return None
            material = Air()
        if not material.passable:
            return None
        if material.material_type.value != "Air":
            if material.material_type.value == "Vault":
                return self.rob_vault()
            return None  # material.passable is bugged, figure out why?
        logger.info(f"{self.player_id} is moving to {x},{y} in house {self.house_id}")
        self.player_location = [x, y]
        db["access"].update_one(
            {"player_id": self.player_id},
            {
                "$set": {
                    "latest_activity": datetime.datetime.now().isoformat(),
                    "player_location": self.player_location
                }
            }
        )
        item = self.render_surroundings(compressed_view=compressed_view)
        item["house_id"] = self.house_id
        item["player_location"] = self.player_location
        return item

    def enter_house(self, compressed_view=False):
        if self.is_in_house():
            return None  # Already in house
        location = [0, 15]
        db["access"].insert_one({
            "player_id": self.player_id,
            "house_id": self.house_id,
            "access_time": datetime.datetime.now().isoformat(),
            "latest_activity": datetime.datetime.now().isoformat(),
            "player_location": location
        })
        self.player_location = location
        item = self.render_surroundings(compressed_view=compressed_view)
        item["house_id"] = self.house_id
        item["player_location"] = location
        return item

    def leave_house(self):
        if not self.is_in_house():
            return True
        db["access"].delete_one({
            "player_id": self.player_id
        })

    @staticmethod
    def visit_too_long(access, house_owner=False):
        if not access:
            return False

        disable_activity_timeout: bool = get_config_value(
            "evictions.disable_timeout", default_value={"value": False}
        ).get("value")
        if disable_activity_timeout:
            return False

        activity_timeout_seconds: int = get_config_value(
            "evictions.activity_timeout_seconds", default_value={"value": 45}
        ).get("value")
        house_owner_access_minutes: int = get_config_value(
            "evictions.house_owner_access_minutes", default_value={"value": 8}
        ).get("value")
        robber_access_minutes: int = get_config_value(
            "evictions.robber_access_minutes", default_value={"value": 10}
        ).get("value")

        latest_activity = datetime.datetime.fromisoformat(access["latest_activity"])
        access_time = datetime.datetime.fromisoformat(access["access_time"])
        now = datetime.datetime.now()
        activity_ago = now - latest_activity
        entered_ago = now - access_time
        if activity_ago > datetime.timedelta(seconds=activity_timeout_seconds):
            return True
        entered_ago_minute_comparison = house_owner_access_minutes if house_owner else robber_access_minutes
        if entered_ago > datetime.timedelta(minutes=entered_ago_minute_comparison):
            return True
        return False

    @staticmethod
    def evict(player_id) -> dict:
        item = db["access"].find_one({"player_id": player_id})
        if not item:
            return {"success": False, "reason": "No player to evict"}
        db["players"].find_one_and_update({"_id": player_id}, {"$set": {"evicted": True}})
        db["access"].delete_one({"player_id": player_id})
        return {"success": True}

    @staticmethod
    def find_occupying_house(player_id) -> Optional[str]:
        item = db["access"].find_one({"player_id": player_id})
        if not item:
            return None
        return item["house_id"]
