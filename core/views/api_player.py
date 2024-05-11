from flask import Blueprint

from utils.api_decorators import player_valid, registration

mod = Blueprint('api_player', __name__)


@mod.route("/api/player/<player_id>")
@player_valid
def get_player(player_id, player):
    return player.as_dict()


@mod.route("/api/player/<player_id>", methods=["POST"])
@registration  # You can create as many players as you want, but we can keep track of who does it :)
def create_player(player_id, player):
    player.save()
    return {"success": True, "player_id": player_id, "token": player.token}
