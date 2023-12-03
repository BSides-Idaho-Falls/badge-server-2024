from flask import Blueprint, send_from_directory

mod = Blueprint('asset', __name__)


@mod.route('/assets/<path:path>')
def assets(path):
    return send_from_directory('static/images/', path)


@mod.route('/js/<path:path>')
def js(path):
    return send_from_directory('static/javascript/', path)


@mod.route('/css/<path:path>')
def css(path):
    return send_from_directory('static/css/', path)
