from flask import Blueprint, send_from_directory, render_template

mod = Blueprint('renders', __name__)


@mod.route('/house/<house_id>')
def assets(house_id):
    return render_template("house_render.html")
