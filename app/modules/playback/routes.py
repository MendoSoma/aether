from flask import Blueprint, render_template

playback_bp = Blueprint('playback_bp', __name__, template_folder='../../templates/playback')

@playback_bp.route('/playback/')
def playback_index():
    return render_template('playback.html')
