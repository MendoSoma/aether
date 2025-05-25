import os
import glob
import json
from flask import Blueprint, jsonify, render_template, request, current_app
from werkzeug.utils import secure_filename
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

@patch_bp.route('/api/fixtures/upload', methods=['POST'])
def upload_fixture_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.endswith('.json'):
        filename = secure_filename(file.filename)
        # Construct the path relative to the 'app' directory
        # current_app.root_path is <project_root>/app
        upload_folder = os.path.join(current_app.root_path, 'fixture_definitions')
        
        # Create the directory if it doesn't exist
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
    # Construct the path relative to the 'app' directory
    # current_app.root_path is <project_root>/app
    fixtures_folder = os.path.join(current_app.root_path, 'fixture_definitions')
    
    if not os.path.isdir(fixtures_folder):
        # If the folder doesn't exist, return an empty list.
        # This is not an error, just means no fixtures have been uploaded yet.
        return jsonify([]) 
        
    fixture_files = glob.glob(os.path.join(fixtures_folder, '*.json'))
    
    fixtures_data = []
    for file_path in fixture_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Extract fixture name (top-level "name" key)
            fixture_name = data.get('name', 'Unknown Fixture')
            
            # Extract channel count from the first mode
            channel_count = 0 # Default if modes are not found or structured as expected
            modes = data.get('modes')
            if modes and isinstance(modes, list) and len(modes) > 0:
                first_mode = modes[0]
                if isinstance(first_mode, dict) and 'channels' in first_mode and isinstance(first_mode['channels'], list):
                    channel_count = len(first_mode['channels'])
            
            fixtures_data.append({
                'fixture_name': fixture_name,
                'channel_count': channel_count,
                # Optionally, include the filename if useful for debugging or frontend keying
                'filename': os.path.basename(file_path) 
            })
        except json.JSONDecodeError:
            # Log this error or handle as appropriate
            print(f"Error decoding JSON from file: {file_path}") 
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
            
    return jsonify(fixtures_data)