# Modular Flask Application for ArtNet

This project provides a modular Flask application structure designed for ArtNet integration. It uses blueprints to organize routes and functionality, making it easy to extend and maintain.

## Project Structure

```
/
├── app/                    # Main application package
│   ├── __init__.py         # Application factory (create_app)
│   ├── modules/            # Directory for application modules (blueprints)
│   │   ├── core/           # Core module for ArtNet API
│   │   │   ├── __init__.py # Makes 'core' a Python package
│   │   │   └── routes.py   # Defines API routes for the 'core' module
│   │   ├── patch/          # Patch module
│   │   │   ├── __init__.py
│   │   │   └── routes.py
│   │   ├── playback/       # Playback module
│   │   │   ├── __init__.py
│   │   │   └── routes.py
│   │   └── programming/    # Programming module
│   │       ├── __init__.py
│   │       └── routes.py
│   ├── static/             # Static files (CSS, JavaScript, images)
│   └── templates/          # HTML templates
│       ├── patch/          # Templates for the patch module
│       │   └── patch.html
│       ├── playback/       # Templates for the playback module
│       │   └── playback.html
│       └── programming/    # Templates for the programming module
│           └── programming.html
├── run.py                  # Script to run the Flask development server
└── README.md               # This file
```

## Core Module API Endpoints

The `core` module provides the following ArtNet related API endpoints under the `/artnet` prefix:

-   **`GET /artnet/api/universes`**: Lists all configured ArtNet universes.
-   **`POST /artnet/api/universes`**: Adds a new ArtNet universe. (Expects JSON payload)
-   **`GET /artnet/api/nodes`**: Lists all discovered ArtNet nodes.
-   **`POST /artnet/api/nodes`**: Configures a new ArtNet node. (Expects JSON payload)

## Feature Modules

This application includes the following feature modules, each with a placeholder HTML page:

-   **Patch Module**: Accessible at `/patch/`. Contains a basic `patch.html`.
    -   Templates: `app/templates/patch/`
-   **Playback Module**: Accessible at `/playback/`. Contains a basic `playback.html`.
    -   Templates: `app/templates/playback/`
-   **Programming Module**: Accessible at `/programming/`. Contains a basic `programming.html`.
    -   Templates: `app/templates/programming/`

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
    The application will start in debug mode, typically on `http://127.0.0.1:5000/`.
    - ArtNet API routes are available under `/artnet/api/...`.
    - Module pages are available (e.g., `http://127.0.0.1:5000/patch/`).

## Adding New Modules (Blueprints)

To add a new module (e.g., a 'custom_feature' module):

1.  **Create a new module directory:**
    `app/modules/custom_feature/`
2.  **Initialize the module package:**
    Create an empty `app/modules/custom_feature/__init__.py`.
3.  **Define routes in `routes.py`:**
    Create `app/modules/custom_feature/routes.py`. Define your blueprint and routes. If rendering HTML, specify the `template_folder`.
    ```python
    # app/modules/custom_feature/routes.py
    from flask import Blueprint, render_template

    custom_bp = Blueprint('custom_bp',
                          __name__,
                          url_prefix='/custom',  # Optional URL prefix for all routes in this blueprint
                          template_folder='../../templates/custom_feature') # Points to app/templates/custom_feature/

    @custom_bp.route('/')
    def index():
        return render_template('custom_page.html')
    ```
4.  **Create Templates:**
    Create your HTML files in the corresponding directory within `app/templates/` (e.g., `app/templates/custom_feature/custom_page.html`).
5.  **Register the new blueprint:**
    In `app/__init__.py`, import and register your new blueprint within the `create_app` function:
    ```python
    # app/__init__.py
    # ... (inside create_app function, after other blueprints)
    from app.modules.custom_feature.routes import custom_bp
    app.register_blueprint(custom_bp)
    ```

This structure allows for clean separation of concerns and makes it straightforward for other developers to contribute new functionalities.
