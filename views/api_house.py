from flask import Blueprint, request

from api.house_base import House
from api.player_base import Player

mod = Blueprint('api_house', __name__)


@mod.route('/api/house/<house_id>', methods=["GET"])
def get_house(house_id):
    house = House(house_id).load()
    if not house:
        return {"success": False, "reason": "House not found"}, 404
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


@mod.route("/api/edit-house/<player_id>/move-vault")
def move_vault(player_id):
    api_token = request.headers.get("X-API-Token")
    player = Player(player_id).load()
    if player.token != api_token:
        return {"success": False, "reason": "Unauthorized"}, 401
    if not player:
        return {"success": False, "reason": "Player doesn't exist"}
    house = House(house_id=player.house_id).load()
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

    success = house.move_vault(data["x"], data["y"])

    return {"success": success}, 200 if success else 400



