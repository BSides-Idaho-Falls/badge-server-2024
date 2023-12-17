import datetime
from typing import Optional, List

from api.house_base import House
from api.material_base import Material
from api.materials import Air
from utils.db_config import db


class HouseAccess:

    def __init__(self, player_id: str, house_id: str):
        self.player_id = player_id
        self.house_id = house_id
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

    def is_in_house(self):
        db_access = db["access"].find_one({
            "player_id": self.player_id
        })
        return True if db_access else False

    def can_enter_house(self):
        db_access = db["access"].find_one({
            "house_id": self.house_id
        })
        return False if db_access else True  # Can't enter while someone else is there

    def render_surroundings(self, player_location: Optional[List[int]] = None, compressed_view: bool = False) -> dict:
        absolute_player_location: Optional[List[int]] = player_location or self.player_location
        if not absolute_player_location:
            return {}
        construction: List[dict] = []
        player_local_location: List[int] = [3, 3]

        remote_x = absolute_player_location[0] - player_local_location[0]
        remote_y = absolute_player_location[1] - player_local_location[1]

        local_x: int = 0
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
        compressed_render = self.get_compressed_render(construction)
        return {"construction": compressed_render if compressed_view else construction}

    def get_compressed_render(self, construction):
        items = []
        for item in construction:
            if item["material_type"].lower() == "vault":
                items.append("v")
                continue
            if item["material_type"].lower() == "player":
                items.append("p")
                continue
            items.append("0" if item["passable"] else "1")
        return "".join(items)

    def move(self, direction):
        direction = direction.lower()
        if direction not in ["left", "right", "up", "down"]:
            return False
        if direction == "left":
            return self.move_left()
        if direction == "right":
            return self.move_right()
        if direction == "up":
            return self.move_up()
        return self.move_down()  # Should always be down because of string whitelist.

    def move_up(self):
        return self._teleport_to(self.player_location[0], self.player_location[1] + 1)

    def move_down(self):
        return self._teleport_to(self.player_location[0], self.player_location[1] - 1)

    def move_left(self):
        return self._teleport_to(self.player_location[0] - 1, self.player_location[1])

    def move_right(self):
        return self._teleport_to(self.player_location[0] + 1, self.player_location[1])

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
            return None  # material.passable is bugged, figure out why?
        print(f"{self.player_id} is moving to {x},{y} in house {self.house_id}")
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

    def enter_house(self):
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
        item = self.render_surroundings()
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
    def evict(player_id) -> dict:
        item = db["access"].find_one({"player_id": player_id})
        if not item:
            return {"success": False, "reason": "No player to evict"}
        db["access"].delete_one({"player_id": player_id})
        return {"success": True}

    @staticmethod
    def find_occupying_house(player_id) -> Optional[str]:
        item = db["access"].find_one({"player_id": player_id})
        if not item:
            return None
        return item["house_id"]
