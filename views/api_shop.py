from flask import Blueprint

from api.house_base import House, VaultContents
from api.material_base import MaterialType, Material
from api.materials import material_from_type
from utils import metrics
from utils.api_decorators import has_house, json_data
from utils.validation import dict_types_valid

mod = Blueprint('api_shop', __name__)


@mod.route("/api/shop/<player_id>/purchase", methods=["POST"])
@json_data
@has_house
def purchase_item(player_id, player, data):

    requested_quantity: int = data.get("quantity", 1)

    if not dict_types_valid(data, {
        "quantity": {
            "type": int
        },
        "material": {
            "type": str,
            "required": True
        }
    }):
        return {"success": False, "reason": "Malformed Data"}, 400

    if requested_quantity < 1 or requested_quantity > 1000:
        return {"success": False, "reason": "Quantity must be between 1 and 1000"}

    requested_material: MaterialType = MaterialType.from_string(data.get("material"))
    if not requested_material or requested_material in [MaterialType.AIR, MaterialType.VAULT]:
        return {"success": False, "reason": "You can't purchase this!"}

    material: Material = material_from_type(requested_material)
    if not material:
        return {"success": False, "reason": "Nothing to purchase!"}

    if not material.purchasable:
        return {"success": False, "reason": "you aren't allowed to purchase this item!"}

    required_funds: int = material.buy_price * requested_quantity

    house: House = House(house_id=player.house_id).load()
    vault_contents: VaultContents = house.vault_contents

    if required_funds > vault_contents.dollars:
        return {
            "success": False,
            "reason": "You don't have enough money!",
            "cost": required_funds,
            "cost_per_unit": material.buy_price,
            "dollars": vault_contents.dollars,
            "requested_quantity": requested_quantity
        }

    vault_contents.dollars = vault_contents.dollars - required_funds
    vault_contents.increment_material_count(material.material_type, requested_quantity)

    house.save()

    metrics.metric_tracker.set_player_money(player_id, vault_contents.dollars).push()

    return {"success": True, "vault": vault_contents.as_dict()}


@mod.route("/api/shop/<player_id>/sell", methods=["POST"])
@json_data
@has_house
def sell_item(player_id, player, data):

    requested_quantity: int = data.get("quantity", 1)

    if not dict_types_valid(data, {
        "quantity": {
            "type": int
        },
        "material": {
            "type": str,
            "required": True
        }
    }):
        return {"success": False, "reason": "Malformed Data"}, 400

    if requested_quantity < 1 or requested_quantity > 1000:
        return {"success": False, "reason": "Malformed Data"}, 400

    requested_material: MaterialType = MaterialType.from_string(data.get("material"))
    if not requested_material or requested_material in [MaterialType.HOUSE_WALL, MaterialType.AIR, MaterialType.VAULT]:
        return {"success": False, "reason": "You can't sell this!"}

    material: Material = material_from_type(requested_material)
    if not material:
        return {"success": False, "reason": "Nothing to sell!"}

    if not material.sellable:
        return {"success": False, "reason": "you aren't allowed to sell this item!"}

    house: House = House(house_id=player.house_id).load()
    vault_contents: VaultContents = house.vault_contents

    current_quantity = vault_contents.materials.get(data["material"], 0)
    if requested_quantity > current_quantity:
        return {
            "success": False,
            "reason": "You don't have enough material to sell!",
            "requested_quantity_to_sell": requested_quantity,
            "current_quantity": current_quantity,
            "sell_price_per_unit": material.sell_price
        }

    profits = material.sell_price * requested_quantity
    vault_contents.decrement_material_count(material.material_type, requested_quantity)
    vault_contents.dollars = vault_contents.dollars + profits

    house.save()

    metrics.metric_tracker.set_player_money(player_id, vault_contents.dollars).push()

    return {"success": True, "vault": vault_contents.as_dict()}
