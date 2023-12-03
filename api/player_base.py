from typing import Optional

from utils.db_config import db


class Player:

    def __init__(self, player_id: Optional[str] = None):
        self.player_id: Optional[str] = player_id
        self.house_id: Optional[str] = None

    def has_house(self):
        return True if self.house_id else False

    def save(self):
        existing_player = db["players"].find_one({"_id": self.player_id})
        if not existing_player:
            db["players"].insert_one(self.as_dict())
            return self
        db["players"].find_one_and_replace({"_id": self.player_id}, self.as_dict())
        return self

    def load(self):
        player_data = db["players"].find_one({"_id": self.player_id})
        if not player_data:
            return None
        for k, v in player_data.items():
            setattr(self, k, v)
        return self

    def as_dict(self):
        return self.__dict__
