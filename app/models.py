from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from .extensions import db

class Role:
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    # Optional (used for Admin 2FA by email)
    email = db.Column(db.String(255), unique=True, nullable=True, index=True)

    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_by = db.relationship("User", remote_side=[id])

    is_active_paid = db.Column(db.Boolean, default=True)
    paid_until = db.Column(db.DateTime, nullable=True)

    tokens = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, pw: str) -> None:
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw: str) -> bool:
        return check_password_hash(self.password_hash, pw)

    def subscription_ok(self) -> bool:
        if self.role == Role.ADMIN:
            return True
        if not self.is_active_paid:
            return False
        if self.paid_until is None:
            return True
        return datetime.utcnow() <= self.paid_until

    def extend_month(self):
        now = datetime.utcnow()
        base = self.paid_until if (self.paid_until and self.paid_until > now) else now
        self.paid_until = base + timedelta(days=30)
        self.is_active_paid = True

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=1)

class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lesson.id"), nullable=False)
    lesson = db.relationship("Lesson", backref="exercises")

    title = db.Column(db.String(120), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    # optional metadata
    level = db.Column(db.String(32), default="Beginner")
    order = db.Column(db.Integer, default=1)

    tests_py = db.Column(db.Text, nullable=False)
    time_limit_ms = db.Column(db.Integer, default=400)
    token_reward = db.Column(db.Integer, default=1)
    hint = db.Column(db.Text, default="")

    # --- Code-structure rules (checked before running pytest) ---
    require_if = db.Column(db.Boolean, default=False)
    require_else = db.Column(db.Boolean, default=False)
    allow_elif = db.Column(db.Boolean, default=True)

    require_for = db.Column(db.Boolean, default=False)
    require_while = db.Column(db.Boolean, default=False)
    forbid_for = db.Column(db.Boolean, default=False)
    forbid_while = db.Column(db.Boolean, default=False)

    require_function = db.Column(db.Boolean, default=False)
    function_name = db.Column(db.String(64), nullable=True)

    require_print = db.Column(db.Boolean, default=False)
    forbid_print = db.Column(db.Boolean, default=False)
    require_input = db.Column(db.Boolean, default=False)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise.id"), nullable=False)
    student = db.relationship("User", foreign_keys=[student_id])
    exercise = db.relationship("Exercise")

    code_py = db.Column(db.Text, nullable=False)
    # PENDING / FAILED / ERROR / WAITING_APPROVAL / APPROVED / REJECTED
    status = db.Column(db.String(30), default="PENDING")

    runtime_ms = db.Column(db.Integer, nullable=True)
    output = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_id])
    review_note = db.Column(db.Text, default="")
    reviewed_at = db.Column(db.DateTime, nullable=True)

class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    student = db.relationship("User")
    highest_exercise_id = db.Column(db.Integer, default=0)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    sender = db.relationship("User", foreign_keys=[sender_id])
    receiver = db.relationship("User", foreign_keys=[receiver_id])

    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    seen = db.Column(db.Boolean, default=False)

class LabProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    student = db.relationship("User")
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default="")
    filename = db.Column(db.String(255), nullable=False)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
