# app.py
from flask import Flask, jsonify, redirect, url_for
from config import API_V1_STR, PROJECT_NAME  # Import config

# Import blueprints from the routes package
from routes.auth import auth_bp

# Import other blueprints as you create them
from routes.projects import projects_bp
from routes.scans import scans_bp
from routes.reports import reports_bp
from routes.bandit import bandit_bp

# from routes.appointments import appointments_bp
# from routes.dashboard import dashboard_bp

# Optional: Import Flask-CORS if you added it to requirements.txt
from flask_cors import CORS


def create_app():
    app = Flask(__name__)

    # Optional: Configure CORS
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": [
                    "http://localhost:3000",
                    "https://main.d3k1a8dkhmpya0.amplifyapp.com",
                ],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
            }
        },
    )  # Example

    app.config["PROJECT_NAME"] = PROJECT_NAME
    # You can add other configurations here if needed
    # e.g., app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

    # Register Blueprints
    app.register_blueprint(auth_bp)
    # Register other blueprints here
    app.register_blueprint(projects_bp)
    app.register_blueprint(scans_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(bandit_bp)

    @app.route("/api")
    def api_index():
        # Redirect root to a simple API status or docs page if you have one
        return jsonify({"status": f"{app.config['PROJECT_NAME']} API is running"}), 200

    @app.route("/")
    def index():
        return redirect("/api")

    # Add a simple error handler for demonstration
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not Found"}), 404

    return app


if __name__ == "__main__":
    app = create_app()
    # Use Flask's development server
    # host='0.0.0.0' makes it accessible externally, debug=True enables auto-reload
    app.run(host="0.0.0.0", port=5001, debug=True)
