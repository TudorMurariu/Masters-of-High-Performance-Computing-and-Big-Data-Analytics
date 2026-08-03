"""
app.py  --  BotFarm Simulator Flask Application
"""
import os
import sys
import logging
from flask import Flask
from flask_cors import CORS
from sqlalchemy import text
from extensions import db

# ── Logging ────────────────────────────────────────────────────────────────────
# Force line-buffered stdout so background-thread logs appear immediately
# in the Werkzeug dev-server console (PYTHONUNBUFFERED fix).
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(line_buffering=True)
        sys.stderr.reconfigure(line_buffering=True)
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
    force=True,           # override any handler Flask already added
    stream=sys.stdout,
)


def _migrate(db):
    """Add new columns to existing SQLite DB without wiping data."""
    migrations = [
        "ALTER TABLE bots  ADD COLUMN pic_status   VARCHAR(10) DEFAULT 'ready'",
        "ALTER TABLE posts ADD COLUMN post_status  VARCHAR(10) DEFAULT 'ready'",
    ]
    with db.engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                pass  # column already exists

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "botfarm2024")


def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="/static")

    app.secret_key = os.environ.get("SECRET_KEY", "botfarm-secret-key-change-in-prod")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///botfarm.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    CORS(app, supports_credentials=True, origins=["http://localhost:5173"])
    db.init_app(app)

    # Ensure upload dirs exist
    for folder in ("profile_pics", "videos"):
        os.makedirs(os.path.join(app.root_path, "static", folder), exist_ok=True)

    # Create tables + migrate new columns into existing DB
    with app.app_context():
        import models  # noqa: F401 — registers ORM models
        db.create_all()
        _migrate(db)

    # Register blueprints
    from routes.auth     import auth_bp
    from routes.bots     import bots_bp
    from routes.generate import generate_bp
    from routes.chat     import chat_bp
    from routes.posts    import posts_bp
    from routes.detect   import detect_bp
    from routes.schedule import schedule_bp

    app.register_blueprint(auth_bp,     url_prefix="/api/auth")
    app.register_blueprint(bots_bp,     url_prefix="/api/bots")
    app.register_blueprint(generate_bp, url_prefix="/api/generate")
    app.register_blueprint(chat_bp,     url_prefix="/api/chat")
    app.register_blueprint(posts_bp,    url_prefix="/api/posts")
    app.register_blueprint(detect_bp,   url_prefix="/api/detect")
    app.register_blueprint(schedule_bp, url_prefix="/api/schedule")

    # Re-arm schedules that were active when Flask last ran
    from services.scheduler_service import restart_all
    restart_all(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000, threaded=True)
