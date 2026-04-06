from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.extensions import init_supabase


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # CORS — allow frontend origin
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:5173"],
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
        }
    })

    # Initialize Supabase
    init_supabase()

    # Register blueprints
    from app.routes.tickets import tickets_bp
    from app.routes.users import users_bp
    from app.routes.ai import ai_bp
    from app.routes.metrics import metrics_bp
    from app.routes.github import github_bp
    from app.routes.admin import admin_bp
    from app.routes.attachments import attachments_bp

    app.register_blueprint(tickets_bp, url_prefix="/api")
    app.register_blueprint(users_bp, url_prefix="/api")
    app.register_blueprint(ai_bp, url_prefix="/api")
    app.register_blueprint(metrics_bp, url_prefix="/api")
    app.register_blueprint(github_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api")
    app.register_blueprint(attachments_bp, url_prefix="/api")

    @app.route("/api/health")
    def health():
        return {"status": "ok", "service": "NDMG Task Manager API"}

    return app
