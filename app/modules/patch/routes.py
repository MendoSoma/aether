from flask import Blueprint, jsonify, render_template
from app.classes import Helper

patch_bp = Blueprint('patch_bp', __name__, template_folder='../../templates/patch')

@patch_bp.route('/patch/')
def patch_index():
    # No need to fetch nodes; JavaScript handles it
    return render_template('patch.html')

@patch_bp.route('/api/nodes')
def get_nodes():
    nodes = Helper.discover_artnet_nodes(ip_address='192.168.1.100', timeout=2.0)
    return jsonify(nodes)