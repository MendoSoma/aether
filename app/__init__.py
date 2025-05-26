from flask import Flask
from app.modules.patch.routes import PatchManager

def create_app():
    app = Flask(__name__)
    app.patch_manager = PatchManager()  # Attach to app

    # Configuration can be added here, e.g., app.config.from_object('config.Config')

    # Import and register patch blueprint
    from app.modules.patch.routes import patch_bp
    app.register_blueprint(patch_bp)

    # Import and register playback blueprint
    from app.modules.playback.routes import playback_bp
    app.register_blueprint(playback_bp)

    # Import and register programming blueprint
    from app.modules.programming.routes import programming_bp
    app.register_blueprint(programming_bp)

    return app