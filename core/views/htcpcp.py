from flask import Blueprint

mod = Blueprint('api_htcpcp', __name__)


@mod.route("/coffee", methods=["BREW", "POST"])
def brew_coffee():
    valid_additions: list = [
        "Cream", "Whole Milk", "Vanilla", "Raspberry", "Whisky", "Aquavit"
    ]
    return {
        "success": False, "reason": "I'm a teapot, short and stout.",
        "valid_additions": valid_additions
    }, 418


@mod.route("/coffee", methods=["GET"])
def get_coffee():
    return {"success": False, "reason": "I'm a teapot, short and stout."}, 418


@mod.route("/coffee", methods=["WHEN"])
def say_when():
    return {"success": False, "reason": "I'm a teapot, short and stout."}, 418

