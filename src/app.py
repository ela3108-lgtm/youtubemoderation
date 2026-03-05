from flask import Flask, redirect, url_for
from routes.api_routes import api
from routes.dashboard_routes import dashboard
from routes.moderation_routes import moderation
from database import init_database
import os


def create_app():
    # ------------------------------
    # Correct static + template path
    # ------------------------------
    base_dir = os.path.dirname(os.path.abspath(__file__))

    app = Flask(
        __name__,
        static_folder=os.path.join(base_dir, "static"),
        template_folder=os.path.join(base_dir, "templates")
    )

    # ------------------------------
    # Initialize Database
    # ------------------------------
    init_database()

    # ------------------------------
    # Register Blueprints
    # ------------------------------
    app.register_blueprint(api, url_prefix="/api")
    app.register_blueprint(dashboard)             # NO PREFIX → /dashboard works
    app.register_blueprint(moderation, url_prefix="/moderation")

    # ------------------------------
    # Homepage (redirect to dashboard)
    # ------------------------------
    @app.route("/")
    def home():
        return redirect(url_for("dashboard.show_dashboard"))

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)