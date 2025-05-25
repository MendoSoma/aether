from flask import Blueprint, jsonify, request

core_bp = Blueprint('core_bp', __name__) # The url_prefix='/artnet' is defined during blueprint registration in app/__init__.py

@core_bp.route('/api/universes', methods=['GET'])
def get_universes():
    # Placeholder for ArtNet universe data
    return jsonify({"message": "List of all configured ArtNet universes"})

@core_bp.route('/api/universes', methods=['POST'])
def add_universe():
    # Placeholder for adding a new universe
    # data = request.json # Assuming JSON payload
    return jsonify({"message": "New ArtNet universe added (placeholder)", "data": request.json}), 201

@core_bp.route('/api/nodes', methods=['GET'])
def get_nodes():
    # Placeholder for ArtNet node data
    return jsonify({"message": "List of all ArtNet nodes"})

@core_bp.route('/api/nodes', methods=['POST'])
def add_node():
    # Placeholder for configuring a new node
    # data = request.json # Assuming JSON payload
    return jsonify({"message": "New ArtNet node configured (placeholder)", "data": request.json}), 201