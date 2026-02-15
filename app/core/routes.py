from flask import Blueprint, render_template, request
from flask_login import current_user
from ..decorators import role_required
from ..models import Role, User, Lesson, Exercise, Submission, Progress
from ..extensions import db
from ..services.gating import progress_stats

core_bp = Blueprint("core", __name__)

@core_bp.get("/")
def index():
    if not current_user.is_authenticated:
        from flask import redirect, url_for
        return redirect(url_for("auth.login_selector"))
    # redirect to role dashboards
    from flask import redirect, url_for
    if current_user.role == Role.ADMIN:
        return redirect(url_for("admin.dashboard"))
    if current_user.role == Role.TEACHER:
        return redirect(url_for("teacher.dashboard"))
    return redirect(url_for("student.dashboard"))

@core_bp.get("/search")
@role_required(Role.ADMIN, Role.TEACHER, Role.STUDENT)
def search():
    q = (request.args.get("q") or "").strip()
    users = lessons = exercises = []
    if q:
        users = User.query.filter(User.username.contains(q)).limit(30).all()
        lessons = Lesson.query.filter(Lesson.title.contains(q)).limit(30).all()
        exercises = Exercise.query.filter(Exercise.title.contains(q)).limit(30).all()
    return render_template("search.html", q=q, users=users, lessons=lessons, exercises=exercises)

@core_bp.get("/api/stats")
@role_required(Role.ADMIN, Role.TEACHER, Role.STUDENT)
def api_stats():
    # counts for charts; teacher/student have scoped stats
    role = current_user.role
    if role == Role.ADMIN:
        data = {
            "users": User.query.count(),
            "teachers": User.query.filter_by(role=Role.TEACHER).count(),
            "students": User.query.filter_by(role=Role.STUDENT).count(),
            "lessons": Lesson.query.count(),
            "exercises": Exercise.query.count(),
            "submissions": Submission.query.count(),
        }
    elif role == Role.TEACHER:
        my_students = User.query.filter_by(role=Role.STUDENT, created_by_id=current_user.id).count()
        data = {
            "users": my_students,
            "teachers": 1,
            "students": my_students,
            "lessons": Lesson.query.count(),
            "exercises": Exercise.query.count(),
            "submissions": Submission.query.join(User, Submission.student_id==User.id).filter(User.created_by_id==current_user.id).count(),
        }
    else:
        passed, _total = progress_stats(current_user.id)
        data = {
            "users": 1,
            "teachers": 0,
            "students": 1,
            "lessons": Lesson.query.count(),
            "exercises": Exercise.query.count(),
            "submissions": Submission.query.filter_by(student_id=current_user.id).count(),
            "passed": passed,
            "tokens": current_user.tokens or 0
        }
    from flask import jsonify
    return jsonify(data)
