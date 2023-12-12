import json
import uuid
from typing import Optional, Union, List

from api.material_base import MaterialType, Material
from api.materials import Air
from utils.db_config import db

MIX_X = 0
MIN_Y = 0
MAX_X = 30
MAX_Y = 30


class VaultContents:

    def __init__(self):
        self.dollars: int = 2000  # Starting money
        self.materials: dict = {}
        for item in MaterialType:
            self.materials[item.value.replace(" ", "_")] = 0
        self.materials["Wooden_Wall"] = 20 # Start with 20 walls

    def load(self, json_value):
        self.dollars = json_value.get("dollars", 2000)  # Starting money if DB value is null
        for item in MaterialType:
            count = json_value.get(item.value.replace(" ", "_"), 0)
            self.materials[item.value.replace(" ", "_")] = count
        return self

    def set_material_count(self, material_type: Union[MaterialType, str], count: int):
        if isinstance(material_type, MaterialType):
            material_type = material_type.value
        self.materials[material_type] = count

    def decrement_material_count(self, material_type: Union[MaterialType, str]):
        if isinstance(material_type, MaterialType):
            material_type = material_type.value
        if material_type not in self.materials:
            return False
        if self.materials[material_type] > 0:
            return False
        self.set_material_count(material_type, self.materials[material_type] - 1)
        return True

    def increment_material_count(self, material_type: Union[MaterialType, str]):
        if isinstance(material_type, MaterialType):
            material_type = material_type.value
        if material_type not in self.materials:
            self.materials[material_type] = 1
            return True
        self.set_material_count(material_type, self.materials[material_type] + 1)
        return True

    def as_dict(self):
        return self.__dict__


class House:

    def __init__(self, house_id: Optional[str] = None):
        self.house_id: Optional[str] = house_id
        self.metadata: dict = {}

        self.vault_contents: Optional[VaultContents] = VaultContents()

        # List of materials which constructs the api
        # 0,0 -> 30,30: Inclusive of 0 and 30: default AIR
        self.construction: list = [
            {
                "material_type": MaterialType.VAULT,
                "location": [30, 15]
            }
        ]

    @staticmethod
    def _in_bounds(x: int, y: int):
        return not (x < MIX_X or x > MAX_X or MIN_Y < 0 or y > MAX_Y)

    def move_vault(self, x: int, y: int) -> bool:
        material: Optional[Material] = self.get_material_from(x, y)
        if not material or material.material_type != MaterialType.AIR:
            return False
        construction_list: List[dict] = []
        for item in self.construction:
            if item["material_type"] != MaterialType.VAULT:
                construction_list.append(item)
        construction_list.append({
            "material_type": MaterialType.VAULT,
            "location": [x, y]
        })
        return True

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
        if not House._in_bounds(x, y):
            return None
        for item in self.construction:
            location = item["location"]
            if x == location[0] and y == location[1]:
                return item
        return Air()  # Default material in a api

    def remove_item(self, x: int, y: int):
        new_construction: List[dict] = []
        removed: Optional[dict] = None
        for item in self.construction:
            location = item["location"]
            if x == location[0] and y == location[1]:
                removed = item
                continue
            new_construction.append(item)
        self.construction = new_construction
        return removed

    def set_item(self, material_type: Union[MaterialType, str], x: int, y: int):
        current_item: Material = self.get_material_from(x, y)
        if not House._in_bounds(x, y):
            return False, None
        if isinstance(material_type, str):
            material_type = MaterialType.from_string(material_type)
        if current_item.material_type == MaterialType.VAULT:
            return False, None
        removed: Optional[dict] = self.remove_item(x, y)
        if material_type != MaterialType.AIR:
            self.construction.append({
                "material_type": material_type,
                "location": [x, y]
            })
        return True, removed

    def as_dict(self) -> dict:
        """Conversion to dict for friendliness with mongo."""
        values: dict = self.__dict__
        values["_id"] = self.house_id
        c2: list = []
        for item in self.construction:
            item["material_type"] = item["material_type"].value
            c2.append(item)
        values["construction"] = c2
        values["vault_contents"] = self.vault_contents.as_dict()
        return values

    def load(self):
        if not self.house_id:
            return None
        house: dict = db["houses"].find_one({"_id": self.house_id})
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
        vault_contents_dict = item.get("vault_contents", {})
        self.vault_contents = VaultContents().load(vault_contents_dict)
        return self



