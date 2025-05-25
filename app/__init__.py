from flask import Flask

def create_app():
    app = Flask(__name__)

    # Configuration can be added here, e.g., app.config.from_object('config.Config')

    # Import and register blueprints
    from app.modules.core.routes import core_bp
    app.register_blueprint(core_bp, url_prefix='/artnet') # Example prefix, can be changed

    # Import and register patch blueprint
    from app.modules.patch.routes import patch_bp
    app.register_blueprint(patch_bp) # The patch_bp has its own /patch/ prefix in its routes.

    # Import and register playback blueprint
    from app.modules.playback.routes import playback_bp
    app.register_blueprint(playback_bp) # The playback_bp has its own /playback/ prefix in its routes.

    # Import and register programming blueprint
    from app.modules.programming.routes import programming_bp
    app.register_blueprint(programming_bp) # The programming_bp has its own /programming/ prefix in its routes.

    return app
