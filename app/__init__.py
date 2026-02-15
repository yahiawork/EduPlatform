import os
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from .config import Config
from .extensions import db, login_manager, csrf, limiter
from .models import User
from .services.billing import disable_expired_accounts
from .services.sqlite_schema import ensure_sqlite_schema

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs("instance", exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Create tables (dev-friendly) and patch SQLite schema for older DBs.
    with app.app_context():
        db.create_all()
        try:
            ensure_sqlite_schema()
        except Exception:
            # Don't crash the app on schema patch failure; routes will show errors.
            pass

    from .auth.routes import auth_bp
    from .admin.routes import admin_bp
    from .teacher.routes import teacher_bp
    from .student.routes import student_bp
    from .chat.routes import chat_bp
    from .lab.routes import lab_bp
    from .core.routes import core_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(core_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(teacher_bp, url_prefix="/teacher")
    app.register_blueprint(student_bp, url_prefix="/student")
    app.register_blueprint(chat_bp, url_prefix="/chat")
    app.register_blueprint(lab_bp, url_prefix="/lab")

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # billing job daily
    scheduler = BackgroundScheduler(daemon=True)
    def _job():
        with app.app_context():
            disable_expired_accounts()
    scheduler.add_job(_job, "interval", hours=24)
    scheduler.start()

    return app
