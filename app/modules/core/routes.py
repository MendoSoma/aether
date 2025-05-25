from flask import Blueprint, jsonify

core_bp = Blueprint('core_bp', __name__)

@core_bp.route('/universes')
def get_universes():
    # Placeholder for ArtNet universe data
    return jsonify({"message": "List of ArtNet universes"})

@core_bp.route('/nodes')
def get_nodes():
    # Placeholder for ArtNet node data
    return jsonify({"message": "List of ArtNet nodes"})
