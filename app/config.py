import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///../instance/app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "instance/uploads")
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  


    GRADER_TIMEOUT_SEC = int(os.environ.get("GRADER_TIMEOUT_SEC", "6"))
    USE_DOCKER_GRADER = False

    DOCKER_IMAGE = os.environ.get("DOCKER_IMAGE", "edu_runner:latest")


    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "0") == "1"


    SMTP_HOST = os.environ.get("SMTP_HOST", "")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASS = os.environ.get("SMTP_PASS", "")
    SMTP_FROM = os.environ.get("SMTP_FROM", SMTP_USER)
    SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "1") == "1"

    ADMIN_OTP_TTL_SEC = int(os.environ.get("ADMIN_OTP_TTL_SEC", "300"))
    DEBUG = False
