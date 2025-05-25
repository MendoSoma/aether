from flask import Blueprint, render_template

programming_bp = Blueprint('programming_bp', __name__, template_folder='../../templates/programming')

@programming_bp.route('/programming/')
def programming_index():
    return render_template('programming.html')
