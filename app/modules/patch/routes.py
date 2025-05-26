import os
import glob
import json
import socket
import struct
import time
import uuid
from flask import Blueprint, jsonify, render_template, request, current_app
from werkzeug.utils import secure_filename
import logging

logging.basicConfig(filename='debug.log', level=logging.DEBUG)

patch_bp = Blueprint('patch_bp', __name__, template_folder='../../templates/patch')

class PatchManager:
    def __init__(self):
        self.nodes = {}  # {node_id: {name, ip, universe_count}}
        self.universes = {}  # {universe_id: {node_id, fixtures}}
        self.fixtures = {}  # {fixture_id: {name, channels, universe_id, start_address}}

    def add_node(self, node_id, name, ip, universe_count):
        self.nodes[str(node_id)] = {"name": name, "ip": ip, "universe_count": universe_count}

    def add_universe(self, universe_id, node_id=None):
        self.universes[str(universe_id)] = {"node_id": node_id, "fixtures": []}

    def patch_fixture(self, fixture_id, name, channels, universe_id, start_address, quantity=1):
        if not isinstance(self.universes, dict):
            logging.error("PatchManager universes is not a dictionary")
            raise ValueError("PatchManager universes is not a dictionary")
        universe_id = str(universe_id)
        if universe_id not in self.universes:
            return False, "Universe does not exist"
        if not (1 <= start_address <= 512):
            return False, "Start address must be between 1 and 512"
        if start_address + (channels * quantity) - 1 > 512:
            return False, "Channels exceed universe capacity"

        for fix in self.fixtures.values():
            if fix["universe_id"] == universe_id:
                existing_start = fix["start_address"]
                existing_end = existing_start + fix["channels"] - 1
                for i in range(quantity):
                    new_start = start_address + (i * channels)
                    new_end = new_start + channels - 1
                    if not (new_end < existing_start or new_start > existing_end):
                        return False, "Channel overlap detected"

        for i in range(quantity):
            fid = f"{fixture_id}-{uuid.uuid4()}" if quantity > 1 else fixture_id
            self.fixtures[fid] = {
                "name": name,
                "channels": channels,
                "universe_id": universe_id,
                "start_address": start_address + (i * channels)
            }
            self.universes[universe_id]["fixtures"].append(fid)
        print(
        f"[NODES]{json.dumps(self.nodes, indent=2)}[END NODES]\n"
        f"[UNIVERSES]{json.dumps(self.universes, indent=2)}[END UNIVERSES]\n"
        f"[FIXTURES]{json.dumps(self.fixtures, indent=2)}[END FIXTURES]"
        )    
        return True, "Fixture(s) patched successfully"

    def get_state(self):
        return {
            "nodes": self.nodes,
            "universes": self.universes,
            "fixtures": self.fixtures
        }

def discover_artnet_nodes(ip_address: str = "192.168.1.100", timeout: float = 2.0):
    ARTNET_PORT = 6454
    broadcast_ip = ip_address.rsplit('.', 1)[0] + '.255'
    logging.info(f"Using broadcast IP: {broadcast_ip}")
    # Placeholder; replace with actual implementation from app/classes.py
    return [
        {"name": "ICERAY NODE 1", "ip": "192.168.1.201", "universe_count": 2}
    ]

@patch_bp.route('/patch/')
def patch_index():
    return render_template('patch.html')

@patch_bp.route('/api/nodes')
def get_nodes():
    nodes = discover_artnet_nodes(ip_address='192.168.1.100', timeout=2.0)
    for i, node in enumerate(nodes):
        current_app.patch_manager.add_node(str(i), node['name'], node['ip'], node['universe_count'])
        for u in range(node['universe_count']):
            current_app.patch_manager.add_universe(str(i * 100 + u))
    return jsonify(nodes)

@patch_bp.route('/api/patch', methods=['POST'])
def patch_fixture():
    try:
        data = request.get_json()
        logging.debug(f"Patch payload: {data}")
        if not data:
            return jsonify({"error": "No JSON payload provided"}), 400

        required_fields = ['fixture_id', 'universe_id', 'start_address', 'quantity']
        if not all(field in data for field in required_fields):
            return jsonify({"error": f"Missing required fields: {', '.join(f for f in required_fields if f not in data)}"}), 400

        fixture_id = str(data['fixture_id'])
        universe_id = str(data['universe_id'])
        start_address = int(data['start_address'])
        quantity = int(data['quantity'])

        fixture_path = os.path.join('app/fixture_definitions', f"{fixture_id}")
        if not os.path.exists(fixture_path):
            return jsonify({"error": "Fixture definition not found"}), 404
        with open(fixture_path, 'r') as f:
            fixture_data = json.load(f)
        logging.debug(f"Fixture data: {fixture_data}")

        if 'name' not in fixture_data or 'modes' not in fixture_data or not fixture_data['modes']:
            return jsonify({"error": "Invalid fixture definition: missing name or modes"}), 400

        selected_mode = fixture_data['modes'][0]
        channels = len(selected_mode['channels'])
        if channels <= 0:
            return jsonify({"error": "Invalid channel count in first mode"}), 400

        fixture_name = fixture_data['name']

        success, message = current_app.patch_manager.patch_fixture(
            fixture_id, fixture_name, channels, universe_id, start_address, quantity
        )
        if success:
            return jsonify({"message": message}), 200
        else:
            return jsonify({"error": message}), 400
    except ValueError as e:
        logging.error(f"ValueError in patch: {str(e)}")
        return jsonify({"error": "Invalid input: " + str(e)}), 400
    except Exception as e:
        logging.error(f"Exception in patch: {str(e)}")
        return jsonify({"error": "Server error: " + str(e)}), 500

@patch_bp.route('/api/fixtures/upload', methods=['POST'])
def upload_fixture_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.endswith('.json'):
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(current_app.root_path, 'fixture_definitions')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        
        try:
            file.save(file_path)
            return jsonify({'message': f'File "{filename}" uploaded successfully'})
        except Exception as e:
            return jsonify({'error': f'Error saving file: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Invalid file type, only .json files are allowed'}), 400

@patch_bp.route('/api/fixtures', methods=['GET'])
def list_fixtures():
    fixtures_folder = os.path.join(current_app.root_path, 'fixture_definitions')
    if not os.path.isdir(fixtures_folder):
        return jsonify([])
    
    fixture_files = glob.glob(os.path.join(fixtures_folder, '*.json'))
    fixtures_data = []
    for file_path in fixture_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            fixture_name = data.get('name', 'Unknown Fixture')
            channel_count = 0
            modes = data.get('modes')
            if modes and isinstance(modes, list) and len(modes) > 0:
                first_mode = modes[0]
                if isinstance(first_mode, dict) and 'channels' in first_mode and isinstance(first_mode['channels'], list):
                    channel_count = len(first_mode['channels'])
            
            fixtures_data.append({
                'fixture_name': fixture_name,
                'channel_count': channel_count,
                'filename': os.path.basename(file_path)
            })
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error for {file_path}: {str(e)}")
        except Exception as e:
            logging.error(f"Error processing {file_path}: {str(e)}")
            
    return jsonify(fixtures_data)

@patch_bp.route('/api/fixtures/<fixture_id>', methods=['GET'])
def get_fixture(fixture_id):
    fixture_path = os.path.join(current_app.root_path, 'fixture_definitions', f"{fixture_id}.json")
    if not os.path.exists(fixture_path):
        return jsonify({"error": "Fixture not found"}), 404
    with open(fixture_path, 'r') as f:
        return jsonify(json.load(f))