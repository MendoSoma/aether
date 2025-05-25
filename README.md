# Modular Flask Application for ArtNet

This project provides a modular Flask application structure designed for ArtNet integration. It uses blueprints to organize routes and functionality, making it easy to extend and maintain.

## Project Structure

```
/
├── app/                    # Main application package
│   ├── __init__.py         # Application factory (create_app)
│   ├── modules/            # Directory for application modules (blueprints)
│   │   └── core/           # Example 'core' module for ArtNet
│   │       ├── __init__.py # Makes 'core' a Python package
│   │       └── routes.py   # Defines routes for the 'core' module
│   ├── static/             # Static files (CSS, JavaScript, images)
│   └── templates/          # HTML templates
├── run.py                  # Script to run the Flask development server
└── README.md               # This file
```

## Running the Application

1.  **Ensure Python and Flask are installed.**
    If not, install Flask:
    ```bash
    pip install Flask
    ```
2.  **Navigate to the project root directory.**
3.  **Run the application:**
    ```bash
    python run.py
    ```
    The application will start in debug mode, typically on `http://127.0.0.1:5000/`. The ArtNet routes will be available under the `/artnet` prefix (e.g., `http://127.0.0.1:5000/artnet/universes`).

## Adding New Modules (Blueprints)

To add a new module (e.g., a 'lighting_effects' module):

1.  **Create a new module directory:**
    Inside `app/modules/`, create a new directory for your module (e.g., `app/modules/lighting_effects/`).
2.  **Initialize the module package:**
    Create an empty `__init__.py` file within your new module directory (e.g., `app/modules/lighting_effects/__init__.py`).
3.  **Define routes in `routes.py`:**
    Create a `routes.py` file in your module directory (e.g., `app/modules/lighting_effects/routes.py`). Define your blueprint and routes here:

    ```python
    # app/modules/lighting_effects/routes.py
    from flask import Blueprint, jsonify

    lighting_bp = Blueprint('lighting_bp', __name__, url_prefix='/lighting')

    @lighting_bp.route('/strobe')
    def strobe_effect():
        return jsonify({"effect": "strobe activated"})

    # Add other lighting effect routes here...
    ```
4.  **Register the new blueprint:**
    In `app/__init__.py`, import and register your new blueprint within the `create_app` function:

    ```python
    # app/__init__.py
    from flask import Flask

    def create_app():
        app = Flask(__name__)

        # ... (other configurations)

        # Import and register core blueprint
        from app.modules.core.routes import core_bp
        app.register_blueprint(core_bp, url_prefix='/artnet')

        # Import and register your new blueprint
        from app.modules.lighting_effects.routes import lighting_bp # Adjust import path
        app.register_blueprint(lighting_bp) # url_prefix is already in blueprint definition

        return app
    ```

This structure allows for clean separation of concerns and makes it straightforward for other developers to contribute new functionalities by adding their own modules.
