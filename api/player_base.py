import datetime
import uuid
from typing import Optional

from utils.db_config import db


class Player:

    def __init__(self, player_id: Optional[str] = None, registered_by: Optional[str] = None):
        self.player_id: Optional[str] = player_id
        self.house_id: Optional[str] = None
        self.token: str = str(uuid.uuid4())
        self.registered_by: str = registered_by
        self.last_robbery_attempt: Optional[datetime] = None

    def has_house(self):
        return True if self.house_id else False

    def can_rob_house(self) -> int:
        if not self.last_robbery_attempt:
            return 0
        now = datetime.datetime.now()
        difference = now - self.last_robbery_attempt
        if difference < datetime.timedelta(seconds=45):
            seconds: int = difference.seconds
            return seconds
        return 0

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
            if k == "last_robbery_attempt":
                setattr(self, k, datetime.datetime.fromisoformat(v))
                continue
            setattr(self, k, v)
        return self

    def as_dict(self):
        item = self.__dict__
        item["_id"] = self.player_id
        if self.last_robbery_attempt:
            item["last_robbery_attempt"] = datetime.datetime.isoformat(self.last_robbery_attempt)
        return item
