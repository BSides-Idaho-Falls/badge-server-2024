from flask import Blueprint

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



