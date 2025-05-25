from flask import Flask

def create_app():
    app = Flask(__name__)

    # Configuration can be added here, e.g., app.config.from_object('config.Config')

    # Import and register blueprints
    from app.modules.core.routes import core_bp
    app.register_blueprint(core_bp, url_prefix='/artnet') # Example prefix, can be changed

    return app
