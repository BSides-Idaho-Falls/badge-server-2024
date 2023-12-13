from typing import Optional

from flask import Blueprint

from api.house_tracking import HouseAccess
from utils.api_decorators import has_house

mod = Blueprint('api_game', __name__)


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
    response = access.enter_house()
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
        # Shouldn't happen. Access was there, but house no longer exist.
        # Evict player from deleted house
        HouseAccess.evict(player_id)
        return {"success": False, "reason": "House does not exist!"}, 404
    access.leave_house()
    return {"success": True}


@mod.route("/api/game/<player_id>/rob_house", methods=["POST"])
@has_house
def rob_house(player_id, player):

    return {"success": True}
