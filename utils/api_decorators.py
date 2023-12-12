import inspect

from flask import request

from api.house_base import House
from api.player_base import Player
from utils.db_config import db


def _signature_contains_value(signature, value):
    return any(param for param in signature.parameters.values() if param.name.lower() == value)


def has_house(func):

    def validate_incoming_data(player_id):
        api_token: str = request.headers.get("X-API-Token")
        player: Player = Player(player_id).load()
        if player.token != api_token:
            return {"success": False, "reason": "Unauthorized"}, 401
        if not player:
            return {"success": False, "reason": "Player doesn't exist"}
        house: House = House(house_id=player.house_id).load()
        if not house:
            return {"success": False, "reason": "House not found."}, 404

        return {"success": True, "player": player}, 200

    def decorator(*args, **kwargs):
        _coarg = func.__code__.co_argcount
        _arg = _coarg > 0
        signature = inspect.signature(func)
        _kwarg = any(
            param for param in signature.parameters.values() if param.kind == param.VAR_KEYWORD
        )
        if not _signature_contains_value(signature, "player_id"):
            return {"success": False, "reason": "Oopsies, an internal error occurred"}
        player_id = args[0] if len(args) > 0 else kwargs["player_id"]
        if not player_id:
            return {"success": False, "reason": "oops, invalid request"}
        validation_response, code = validate_incoming_data(player_id)
        if not validation_response["success"]:
            return validation_response, code
        kwargs["player"] = validation_response["player"]
        return func(*args, **kwargs) if _arg or _kwarg else func()

    decorator.__name__ = func.__name__
    return decorator


def player_valid(func):

    def validate_incoming_data(player_id):
        api_token: str = request.headers.get("X-API-Token")
        player: Player = Player(player_id).load()
        if not player:
            return {"success": False, "reason": "Player doesn't exist"}, 404
        if player.token != api_token:
            return {"success": False, "reason": "Unauthorized"}, 401

        return {"success": True, "player": player}, 200

    def decorator(*args, **kwargs):
        _coarg = func.__code__.co_argcount
        _arg = _coarg > 0
        signature = inspect.signature(func)
        _kwarg = any(
            param for param in signature.parameters.values() if param.kind == param.VAR_KEYWORD
        )
        print(signature)
        if not _signature_contains_value(signature, "player_id"):
            return {"success": False, "reason": "Oopsies, an internal error occurred"}
        player_id = args[0] if len(args) > 0 else kwargs["player_id"]
        if not player_id:
            return {"success": False, "reason": "oops, invalid request"}
        validation_response, code = validate_incoming_data(player_id)
        if not validation_response["success"]:
            return validation_response, code
        kwargs["player"] = validation_response["player"]
        return func(*args, **kwargs) if _arg or _kwarg else func()

    decorator.__name__ = func.__name__
    return decorator


def registration(func):

    def validate_incoming_data(player_id):
        registration_token: str = request.headers.get("X-Register-Token")
        registration_item = db["registration"].find_one({
            "_id": registration_token
        })
        if not registration_item:
            return {"success": False, "reason": "Invalid registration token"}, 401
        player: Player = Player(player_id).load()
        if player:
            return {"success": False, "reason": "Can't recreate player"}, 400
        player = Player(player_id=player_id, registered_by=registration_token)
        return {"success": True, "player": player}, 200

    def decorator(*args, **kwargs):
        _coarg = func.__code__.co_argcount
        _arg = _coarg > 0
        signature = inspect.signature(func)
        _kwarg = any(
            param for param in signature.parameters.values() if param.kind == param.VAR_KEYWORD
        )
        if not _signature_contains_value(signature, "player_id"):
            return {"success": False, "reason": "Oopsies, an internal error occurred"}
        player_id = args[0] if len(args) > 0 else kwargs["player_id"]
        if not player_id:
            return {"success": False, "reason": "oops, invalid request"}
        validation_response, code = validate_incoming_data(player_id)
        if not validation_response["success"]:
            return validation_response, code
        kwargs["player"] = validation_response["player"]
        return func(*args, **kwargs) if _arg or _kwarg else func()

    decorator.__name__ = func.__name__
    return decorator
