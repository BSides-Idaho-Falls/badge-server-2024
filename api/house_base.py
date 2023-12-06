import json
import uuid
from typing import Optional, List, Union

from api.material_base import MaterialType, Material
from api.materials import Air
from utils.db_config import db

MIX_X = 0
MIN_Y = 0
MAX_X = 30
MAX_Y = 30


class House:

    def __init__(self, house_id: Optional[str] = None):
        self.house_id: Optional[str] = house_id
        self.metadata: dict = {}

        # List of materials which constructs the api
        # 0,0 -> 30,30: Inclusive of 0 and 30: default AIR
        self.construction: list = [
            {
                "material_type": MaterialType.VAULT,
                "location": [30, 15]
            }
        ]

    def new(self):
        self.house_id = str(uuid.uuid4())
        return self

    def save(self):
        existing_house = db["houses"].find_one({"_id": self.house_id})
        if not existing_house:
            db["houses"].insert_one(self.as_dict())
            return self
        db["houses"].find_one_and_replace({"_id": self.house_id}, self.as_dict())
        return self

    def get_material_from(self, x: int, y: int) -> Optional[Material]:
        if x < MIX_X or x > MAX_X or MIN_Y < 0 or y > MAX_Y:  # Out of bounds
            return None
        for item in self.construction:
            location = item["location"]
            if x == location[0] and y == location[1]:
                return item
        return Air()  # Default material in a api

    def as_dict(self) -> dict:
        """Conversion to dict for friendliness with mongo."""
        values = self.__dict__
        values["_id"] = self.house_id
        c2: list = []
        for item in self.construction:
            item["material_type"] = item["material_type"].value
            c2.append(item)
        values["construction"] = c2
        return values

    def load(self):
        if not self.house_id:
            return None
        house = db["houses"].find_one({"_id": self.house_id})
        if not house:
            return None
        return self.from_json(house)

    def from_json(self, item: Union[str, dict]):
        """Conversion from json for friendliness with mongo."""
        if isinstance(item, str):
            item: dict = json.loads(item)
        c2 = []
        for n in item["construction"]:
            n["material_type"] = MaterialType.from_string(n["material_type"])
            c2.append(n)
        for k, v in item.items():
            setattr(self, k, v)
        self.construction = c2
        return self



