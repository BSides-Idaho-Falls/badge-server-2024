from flask import Blueprint

from api.player_base import Player

mod = Blueprint('api_player', __name__)


@mod.route("/api/player/<player_id>")
def get_player(player_id):
    player = Player(player_id).load()
    if not player:
        return {"success": False, "reason": "Player not found"}, 404
    return player.as_dict()


@mod.route("/api/player/<player_id>", methods=["POST"])
def create_player(player_id):
    player = Player(player_id).load()
    if player:
        return {"success": False, "reason": "Can't recreate player"}, 400
    player = Player(player_id)  # .load() would have previously set this object to 'None'
    player.save()
    return {"success": True, "player_id": player_id}


