from flask import Blueprint

from utils.api_decorators import has_house

mod = Blueprint('api_game', __name__)


@mod.route("/api/game/<player_id>/enter_house")
@has_house
def enter_house(player_id, player):

    return {"success": True}


@mod.route("/api/game/<player_id>/rob_house")
@has_house
def rob_house(player_id, player):

    return {"success": True}
