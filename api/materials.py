from api.material_base import Wall, Material, MaterialType


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


class SteelWall(Wall):

    def __init__(self):
        super().__init__()
        self.material_type = MaterialType.STEEL_WALL
        self.name = "Steel Wall"
        self.toughness = 5
        self.conductive = True


class WoodWall(Wall):

    def __init__(self):
        super().__init__()
        self.material_type = MaterialType.WOOD_WALL
        self.name = "Wood Wall"
        self.toughness = 1
