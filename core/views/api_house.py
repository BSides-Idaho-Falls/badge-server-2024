from typing import Tuple

from flask import Blueprint, request

from api.house_base import House, VaultContents
from api.house_tracking import HouseAccess
from api.material_base import Material, MaterialType
from api.materials import Air
from api.player_base import Player
from utils import pathfinder
from utils.api_decorators import has_house, player_valid, json_data
from utils.configuration import get_config_value
from utils.conversions import solution_to_lucky_numbers
from utils.validation import dict_types_valid, evaluate_eviction

mod = Blueprint('api_house', __name__)


@mod.route('/api/house/<player_id>', methods=["GET"])
@has_house
def get_house(player_id, player):
    house: House = House(house_id=player.house_id).load()
    house_dict = house.as_dict()
    del house_dict["_id"]
    return {"success": True, "house": house_dict}


@mod.route('/api/house/<player_id>/vault', methods=["GET"])
@has_house
def get_vault(player_id, player):
    house: House = House(house_id=player.house_id).load()
    vault: dict = house.vault_contents.as_dict()
    condensed: dict = {
        "dollars": vault["dollars"],
        "walls": vault["materials"]["Wooden_Wall"]
    }
    return {"success": True, "vault": condensed}


@mod.route("/api/house/<player_id>", methods=["POST"])
@player_valid
def create_house(player_id, player):
    if player.has_house():
        return {"success": False, "reason": "This player already has a house!"}, 400
    new_house = House().new()
    new_house.save()
    player.house_id = new_house.house_id
    player.save()
    return {"success": True, "house_id": new_house.house_id}


@mod.route("/api/house/<player_id>/abandon", methods=["DELETE"])
@has_house
def abandon_house(player_id, player):
    house = House(house_id=player.house_id).load()
    house.abandoned = True
    house.abandoned_by = player.player_id

    player.house_id = None

    player.save()
    house.save()

    return {
        "success": True,
        "message": "Your house has been abandoned and you lost all "
                   "belongings and money. You may create a new house now and start over."
    }


@mod.route("/api/edit-house/<player_id>/move-vault", methods=["POST"])
@has_house
def move_vault(player_id, player):
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

    access: HouseAccess = HouseAccess(
        player_id=player_id,
        house_id=player.house_id
    ).load()
    if not access:
        return {"success": False, "reason": "House does not exist!"}, 404
    if not access.is_in_house():
        return {"success": False, "reason": "You must be in your own house"}, 400
    if access.house_id != player.house_id:
        return {"success": False, "reason": "You can't be in someone else's house while editing."}, 400

    success: bool = house.move_vault(data["x"], data["y"])  # Solution check is included
    solution = pathfinder.get_maze_solution(house.get_construction_as_dict())
    house.save()

    response = {
        "success": success,
        "lucky_numbers": solution_to_lucky_numbers(solution),
        "house_id": house.house_id,
        "player_location": access.player_location
    }
    access.load()  # Refresh house data
    if evaluate_eviction(player):
        return {"success": False, "reason": "You were kicked out of the house", "e": True}
    surroundings = access.render_surroundings(compressed_view=True)
    return {**response, **surroundings}, 200 if success else 400


@mod.route("/api/edit-house/<player_id>/build", methods=["POST"])
@json_data
@has_house
def build_square(player_id, player, data):
    if "x" not in data or "y" not in data:  # Included for custom error message
        return {
            "success": False,
            "reason": "Malformed Request. Must include 'x' and 'y' coordinates"
        }, 400

    if not dict_types_valid(data, {
        "x": {
            "type": int,
            "required": True
        },
        "y": {
            "type": int,
            "required": True
        },
        "material_type": {
            "type": str,
            "required": True
        }
    }):
        return {"success": False, "reason": "malformed data"}, 400

    x, y = data["x"], data["y"]

    access: HouseAccess = HouseAccess(
        player_id=player_id,
        house_id=player.house_id
    ).load()
    if not access:
        return {"success": False, "reason": "House does not exist!"}, 404
    if not access.is_in_house():
        return {"success": False, "reason": "You must be in your own house"}, 400
    if access.house_id != player.house_id:
        return {"success": False, "reason": "You can't be in someone else's house while editing."}
    if evaluate_eviction(player):
        return {"success": False, "reason": "You were kicked out of the house", "e": True}
    house: House = House(house_id=player.house_id).load()

    if not House.in_bounds(x, y):
        return {"success": False, "reason": "Can't edit out of bounds"}

    material: Material = house.get_material_from(x, y) or Air()

    if material.material_type == MaterialType.VAULT:
        return {
            "success": False, "reason": "Cannot build over the vault. Please move the vault first."
        }

    response_data = {
        "house_id": house.house_id,
        "player_location": access.player_location,
    }

    edit, code = house_editor(house, data)
    access.load()  # Refresh house data
    surroundings = access.render_surroundings(compressed_view=True)
    return {**surroundings, **response_data, **edit}, code


@mod.route("/api/edit-house/<player_id>/clear", methods=["DELETE"])
@json_data
@has_house
def clear_square(player_id, player, data):
    if "x" not in data or "y" not in data:
        return {
            "success": False,
            "reason": "Malformed Request. Must include 'x' and 'y' coordinates"
        }, 400

    if not dict_types_valid(data, {
        "x": {
            "type": int,
            "required": True
        },
        "y": {
            "type": int,
            "required": True
        },
        "material_type": {
            "excluded": True
        }
    }):
        return {"success": False, "reason": "Malformed Data"}, 400

    access: HouseAccess = HouseAccess(
        player_id=player_id,
        house_id=player.house_id
    ).load()
    if not access:
        return {"success": False, "reason": "House does not exist!"}, 404
    if not access.is_in_house():
        return {"success": False, "reason": "You must be in your own house"}, 400
    if access.house_id != player.house_id:
        return {"success": False, "reason": "You can't be in someone else's house while editing."}

    house: House = House(house_id=player.house_id).load()

    response_data = {
        "house_id": house.house_id,
        "player_location": access.player_location,
    }

    edit, code = house_editor(house, data)
    access.load()  # Refresh house data
    if evaluate_eviction(player):
        return {"success": False, "reason": "You were kicked out of the house", "e": True}
    surroundings = access.render_surroundings(compressed_view=True)
    return {**surroundings, **response_data, ** edit}, code


def house_editor(house: House, data: dict) -> Tuple[dict, int]:
    vault_contents: VaultContents = house.vault_contents

    material_type: MaterialType = MaterialType.from_string(
        data.get("material_type")
    )

    if material_type and not vault_contents.decrement_material_count(material_type):
        if material_type == MaterialType.AIR:
            return {"success": False, "reason": "Invalid Material"}, 200
        return {"success": False, "reason": f"You don't have enough {material_type.value}"}, 200

    if not material_type:
        material_type = MaterialType.AIR

    success, removed = house.set_item(material_type, data["x"], data["y"])
    if success and removed:
        vault_contents.increment_material_count(removed["material_type"])
    if not success:
        return {"success": False}, 200
    solution = pathfinder.get_maze_solution(house.get_construction_as_dict())
    if material_type != MaterialType.AIR and not solution:
        return {"success": False, "reason": "No path from door to vault"}, 200
    house.save()
    # Lucky numbers are a list of coordinates with a solution to solve the maze from
    # the door to the vault
    display_lucky_numbers: bool = get_config_value(
        "game.display_lucky_numbers", default_value=True
    ).get("value")
    lucky_numbers = solution_to_lucky_numbers(solution)
    return {"success": success, "lucky_numbers": lucky_numbers if display_lucky_numbers else "0"}, 200
