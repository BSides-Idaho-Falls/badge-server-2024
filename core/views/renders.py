import json

from flask import Blueprint, render_template

from api.house_base import House

mod = Blueprint('renders', __name__)


@mod.route('/house/<house_id>')
def assets(house_id):
    house: House = House(house_id=house_id).load()
    if not house:
        return "404"
    construction = house.as_dict()["construction"]
    data: str = json.dumps({"construction": construction})

    # No api token leaked however the entire house is still leaked both visually,
    # in addition, the json of the house can be grabbed from here, rendering the
    # auth on /api/house/<player_id> useless as long as you know the house_id

    return render_template("house_render.html", house_data=data)
