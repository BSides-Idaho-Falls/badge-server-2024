import inspect
import sys
from typing import Optional

from api.material_base import Wall, Material, MaterialType


def material_from_type(material_type: MaterialType) -> Optional[Material]:
    members = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    import importlib
    for member in members:
        cls_name = member[0]
        try:
            Cls = getattr(importlib.import_module("api.materials"), cls_name)
            instance: Material = Cls()
            if (
                hasattr(instance, "name") and
                instance.material_type == material_type
            ):
                return instance
        except Exception:
            continue
    return None


class Air(Material):

    def __init__(self):
        super().__init__()
        self.material_type = MaterialType.AIR
        self.name = "Air"
        self.toughness = 0
        self.conductive = False


class Vault(Material):

    def __init__(self):
        super().__init__()
        self.material_type = MaterialType.VAULT
        self.name = "Vault"
        self.toughness = 10
        self.conductive = False
        self.passable = False


class HouseWall(Wall):

    def __init__(self):
        super().__init__()
        self.material_type = MaterialType.HOUSE_WALL
        self.name = "House Wall"
        self.toughness = 100
        self.conductive = False
        self.passable = False


class SteelWall(Wall):

    def __init__(self):
        super().__init__()
        self.material_type = MaterialType.STEEL_WALL
        self.name = "Steel Wall"
        self.toughness = 5
        self.conductive = True
        self.passable = False

        self.purchasable = True
        self.sellable = True
        self.sell_price = 40
        self.buy_price = 50


class ConcreteWall(Wall):

    def __init__(self):
        super().__init__()
        self.material_type = MaterialType.CONCRETE_WALL
        self.name = "Concrete Wall"
        self.toughness = 5
        self.conductive = False
        self.passable = False

        self.purchasable = True
        self.sellable = True
        self.sell_price = 40
        self.buy_price = 50


class WoodWall(Wall):

    def __init__(self):
        super().__init__()
        self.material_type = MaterialType.WOOD_WALL
        self.name = "Wood Wall"
        self.toughness = 1
        self.passable = False

        self.purchasable = True
        self.sellable = True
        self.sell_price = 8
        self.buy_price = 10
