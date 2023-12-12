from flask import Blueprint, request

from api.house_base import House
from api.player_base import Player
from utils.api_decorators import has_house

mod = Blueprint('api_shop', __name__)


@mod.route("/api/shop/<player_id>/purchase", methods=["POST"])
@has_house
def purchase_item(player_id, player):
    return {"success": True, "msg": player.as_dict()}


@mod.route("/api/shop/<player_id>/sell", methods=["POST"])
@has_house
def sell_item(player_id, player):
    return {"success": True, "msg": player.as_dict()}
