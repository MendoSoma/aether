from flask import Blueprint, render_template

patch_bp = Blueprint('patch_bp', __name__, template_folder='../../templates/patch') # Define template_folder relative to blueprint

@patch_bp.route('/patch/') # Trailing slash for directory-like access
def patch_index():
    return render_template('patch.html')
