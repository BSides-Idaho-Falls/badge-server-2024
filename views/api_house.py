from typing import Tuple

from flask import Blueprint, request

from api.house_base import House, VaultContents
from api.material_base import Material, MaterialType
from api.player_base import Player
from utils.api_decorators import validator

mod = Blueprint('api_house', __name__)


@mod.route('/api/house/<player_id>', methods=["GET"])
@validator
def get_house(player_id, player):
    house: House = House(house_id=player.house_id).load()
    return {"success": True, "house": house.as_dict()}


@mod.route("/api/house/<player_id>", methods=["POST"])
def create_house(player_id):
    player = Player(player_id=player_id).load()
    if not player:
        return {"success": False, "reason": "Player not found"}, 404
    if player.has_house():
        return {"success": False, "reason": "This player already has a house!"}, 400
    new_house = House().new()
    new_house.save()
    player.house_id = new_house.house_id
    player.save()
    return {"success": True, "house_id": new_house.house_id}


@mod.route("/api/edit-house/<player_id>/move-vault", methods=["POST"])
def move_vault(player_id):
    api_token: str = request.headers.get("X-API-Token")
    player: Player = Player(player_id).load()
    if player.token != api_token:
        return {"success": False, "reason": "Unauthorized"}, 401
    if not player:
        return {"success": False, "reason": "Player doesn't exist"}
    house: House = House(house_id=player.house_id).load()
    if not house:
        return {"success": False, "reason": "House not found."}, 404
    try:
        data: dict = request.get_json(force=True, silent=True)
    except ValueError:
        return {
            "success": False,
            "reason": "Malformed Request. Must include json body"
        }, 400

    if "x" not in data or "y" not in data:
        return {
            "success": False,
            "reason": "Malformed Request. Must include 'x' and 'y' coordinates"
        }, 400

    if not isinstance(data["x"], int) or not isinstance(data["y"], int):
        return {
            "success": False,
            "reason": "Malformed Request. Must include 'x' and 'y' coordinates"
        }, 400

    success: bool = house.move_vault(data["x"], data["y"])

    return {"success": success}, 200 if success else 400


@mod.route("/api/edit-house/<player_id>/build", methods=["POST"])
def build_square(player_id):
    api_token: str = request.headers.get("X-API-Token")
    player: Player = Player(player_id).load()
    if player.token != api_token:
        return {"success": False, "reason": "Unauthorized"}, 401
    if not player:
        return {"success": False, "reason": "Player doesn't exist"}
    house: House = House(house_id=player.house_id).load()
    if not house:
        return {"success": False, "reason": "House not found."}, 404
    try:
        data: dict = request.get_json(force=True, silent=True)
    except ValueError:
        return {
            "success": False,
            "reason": "Malformed Request. Must include json body"
        }, 400

    if "x" not in data or "y" not in data:
        return {
            "success": False,
            "reason": "Malformed Request. Must include 'x' and 'y' coordinates"
        }, 400
    x, y = data["x"], data["y"]
    if not isinstance(x, int) or not isinstance(y, int):
        return {
            "success": False,
            "reason": "Malformed Request. Must include 'x' and 'y' coordinates"
        }, 400

    material: Material = house.get_material_from(x, y)
    if material.material_type == MaterialType.VAULT:
        return {
            "success": False, "reason": "Cannot build over the vault. Please move the vault first."
        }

    if "material_type" not in data:
        return {"success": False, "reason": "No materials given."}

    return house_editor(house, data)


@mod.route("/api/edit-house/<player_id>/clear", methods=["DELETE"])
def clear_square(player_id):
    api_token: str = request.headers.get("X-API-Token")
    player: Player = Player(player_id).load()
    if player.token != api_token:
        return {"success": False, "reason": "Unauthorized"}, 401
    if not player:
        return {"success": False, "reason": "Player doesn't exist"}
    house: House = House(house_id=player.house_id).load()
    if not house:
        return {"success": False, "reason": "House not found."}, 404
    try:
        data: dict = request.get_json(force=True, silent=True)
    except ValueError:
        return {
            "success": False,
            "reason": "Malformed Request. Must include json body"
        }, 400

    if "x" not in data or "y" not in data:
        return {
            "success": False,
            "reason": "Malformed Request. Must include 'x' and 'y' coordinates"
        }, 400
    x, y = data["x"], data["y"]
    if not isinstance(x, int) or not isinstance(y, int):
        return {
            "success": False,
            "reason": "Malformed Request. Must include 'x' and 'y' coordinates"
        }, 400
    if "material_type" in data:
        return {"success": False, "reason": "Can't supply material_type in removal."}, 400
    return house_editor(house, data)


def house_editor(house: House, data: dict) -> Tuple[dict, int]:
    vault_contents: VaultContents = house.vault_contents

    material_type: MaterialType = MaterialType.from_string(
        data.get("material_type", MaterialType.AIR.value)
    )

    if not vault_contents.decrement_material_count(material_type):
        return {"success": False, "reason": f"You don't have enough {material_type.value}"}, 200

    success, removed = house.set_item(material_type, data["x"], data["y"])
    if success and removed:
        vault_contents.increment_material_count(removed["material_type"])
        house.save()
        return {"success": True}, 200

    return {"success": success}, 200
