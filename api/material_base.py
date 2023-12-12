import json
from enum import Enum
from typing import Optional, Union


class MaterialType(Enum):

    AIR = "Air"
    VAULT = "Vault"
    WOOD_WALL = "Wooden Wall"
    STEEL_WALL = "Steel Wall"
    CONCRETE_WALL = "Concrete Wall"

    @staticmethod
    def from_string(name):
        if not name:
            return None

        # If for some reason MaterialType is trying to be reconverted
        if isinstance(name, MaterialType):
            return name

        name = name.replace("_", " ")
        for member in MaterialType.__members__.values():
            if member.value == name:
                return member
        return MaterialType.AIR


class Material:

    def __init__(self):
        self.material_type: Optional[MaterialType] = None
        self.name: Optional[str] = None  # Default Material
        self.passable: bool = True  # Can player pass through?

        self.purchasable: bool = False
        self.sellable: bool = False
        self.sell_price: int = 0
        self.buy_price: int = 0

    def as_dict(self) -> dict:
        values = self.__dict__
        for k, v in values.items():
            if isinstance(v, MaterialType):
                values[k] = v.value
        return values

    def from_json(self, item: Union[str, dict]):
        if isinstance(item, str):
            item: dict = json.loads(item)
        for k, v in item.items():
            if k == "material_type":
                v = MaterialType.from_string(v)
            setattr(self, k, v)
        return self


class Wall(Material):
    def __init__(self):
        super().__init__()
        self.name: Optional[str] = "Wall"
        self.passable: bool = False  # Can a player pass through?
        self.conductive: bool = False  # Can electricity flow through?
        self.toughness: int = 0  # How tough is the wall?
