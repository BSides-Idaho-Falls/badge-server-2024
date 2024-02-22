import datetime
from typing import Optional

from flask import Blueprint, request

from api.house_tracking import HouseAccess
from utils import robbery
from utils.api_decorators import has_house

mod = Blueprint('api_game', __name__)


@mod.route("/api/game/<player_id>/move/<direction>", methods=["POST"])
@has_house
def move_player(player_id, direction, player):
    house_id: Optional[str] = HouseAccess.find_occupying_house(player_id)
    if not house_id:
        return {"success": False, "reason": "You are not in a house."}, 400
    access: HouseAccess = HouseAccess(
        player_id=player_id,
        house_id=house_id
    ).load()
    compressed_view = False
    if direction.endswith("-c"):
        compressed_view = True
        direction = direction.replace("-c", "")
    if not access:
        return {"success": False, "reason": "House does not exist!"}, 404
    if direction.lower() not in ["left", "right", "up", "down"]:
        return {"success": False, "reason": "Illegal direction"}, 400
    item = access.move(direction, compressed_view=compressed_view)
    if not item:
        return {"success": False, "reason": "Unable to move in that direction"}
    item["success"] = True
    return item


@mod.route("/api/game/<player_id>/enter_house", methods=["POST"])
@has_house
def enter_house(player_id, player):
    """Enter player into his own house."""
    access: HouseAccess = HouseAccess(
        player_id=player_id,
        house_id=player.house_id
    ).load()
    if not access:
        return {"success": False, "reason": "House does not exist!"}, 404
    if access.is_in_house():
        return {"success": False, "reason": "You are already in the house!"}, 400
    if not access.can_enter_house():
        return {"success": False, "reason": "Can't enter house at this time. Is someone there?"}, 401
    compress_header = request.headers.get("c")
    compressed_view = compress_header and compress_header == "y"
    response = access.enter_house(compressed_view=compressed_view)
    if not response:
        return {"success": False, "reason": "Unknown error occurred."}, 500
    response["success"] = True
    return response


@mod.route("/api/game/<player_id>/leave_house", methods=["POST"])
@has_house
def leave_house(player_id, player):
    """Leave house as both an owner and a robber."""
    house_id: Optional[str] = HouseAccess.find_occupying_house(player_id)
    if not house_id:
        return {"success": False, "reason": "You aren't in a house"}, 400
    access: HouseAccess = HouseAccess(
        player_id=player_id,
        house_id=house_id
    ).load()
    if not access:
        # Shouldn't happen. Access was there, but the house no longer exists.
        # Evict player from deleted house
        HouseAccess.evict(player_id)
        return {"success": False, "reason": "House does not exist!"}, 404
    access.leave_house()
    return {"success": True}


@mod.route("/api/game/<player_id>/rob_house", methods=["POST"])
@has_house
def rob_house(player_id, player):
    rob_timeout: int = player.can_rob_house()
    if rob_timeout > 0:
        return {
            "success": False,
            "reason": "You are trying to rob houses too often!",
            "seconds": 45 - rob_timeout
        }
    house_to_rob = robbery.find_unoccupied_house(exclusions=[player.house_id])
    if not house_to_rob:
        return {"success": False, "reason": "There are no available houses to rob!"}
    access: HouseAccess = HouseAccess(
        player_id=player_id,
        house_id=house_to_rob
    ).load()
    if not access:
        return {"success": False, "reason": "House does not exist!"}, 404
    if access.is_in_house():
        return {"success": False, "reason": "You are already in the house!"}, 400
    if not access.can_enter_house():
        return {"success": False, "reason": "Can't enter house at this time. Is someone there?"}, 401
    response = access.enter_house()
    if not response:
        return {"success": False, "reason": "Unknown error occurred."}, 500
    response["success"] = True
    player.last_robbery_attempt = datetime.datetime.now()
    player.save()
    return response
