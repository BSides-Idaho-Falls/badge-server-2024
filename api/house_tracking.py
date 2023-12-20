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
                    construction.append("p" if compressed_view else {
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
                    construction.append("1" if compressed_view else {
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
                    construction.append("1" if compressed_view else {
                        "material_type": material.material_type.value.replace(" ", "_"),
                        "local_location": [local_x, local_y],
                        "absolute_location": [x, y],
                        "passable": passable
                    })
                else:
                    if compressed_view:
                        construction.append("0")
                local_y += 1
            local_x += 1
        #compressed_render = self.get_compressed_render(construction)
        return {"construction": "".join(construction) if compressed_view else construction}

    def get_compressed_render(self, construction):
        items = []
        mapping = {}
        print(construction)
        for _, construction_item in construction:
            print(construction_item)
            x = construction_item["absolute_location"][0]
            y = construction_item["absolute_location"][1]
            mapping[f"{x}-{y}"] = construction_item
        for x in range(0, 30):
            for y in range(0, 30):
                item = mapping.get(f"{x}-{y}")
                if not item:
                    items.append("0")
                else:
                    material_type = item["material_type"].lower()
                    if material_type == "vault":
                        items.append("v")
                    elif material_type == "player":
                        items.append("p")
                    else:
                        items.append("1")
        return "".join(items)

    def move(self, direction, compressed_view=False):
        direction = direction.lower()
        if direction not in ["left", "right", "up", "down"]:
            return False
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
