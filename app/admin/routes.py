from flask import Blueprint, render_template, redirect, url_for, request, flash
from ..decorators import role_required
from ..extensions import db
from ..models import Role, User, Lesson, Exercise

admin_bp = Blueprint("admin", __name__)

@admin_bp.get("/")
@role_required(Role.ADMIN)
def dashboard():
    teachers = User.query.filter_by(role=Role.TEACHER).order_by(User.created_at.desc()).all()
    lessons = Lesson.query.order_by(Lesson.order.asc()).all()
    return render_template("admin_dashboard.html", teachers=teachers, lessons=lessons)

@admin_bp.post("/create-teacher")
@role_required(Role.ADMIN)
def create_teacher():
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    if not username or not password:
        flash("Please fill username and password.")
        return redirect(url_for("admin.dashboard"))
    if User.query.filter_by(username=username).first():
        flash("Username already exists.")
        return redirect(url_for("admin.dashboard"))

    t = User(username=username, role=Role.TEACHER)
    t.set_password(password)
    t.extend_month()
    db.session.add(t)
    db.session.commit()
    flash("Teacher account created.")
    return redirect(url_for("admin.dashboard"))

@admin_bp.post("/create-lesson")
@role_required(Role.ADMIN)
def create_lesson():
    title = (request.form.get("title") or "").strip()
    content = (request.form.get("content") or "").strip()
    order = int(request.form.get("order") or "1")
    if not title or not content:
        flash("Please fill lesson title and content.")
        return redirect(url_for("admin.dashboard"))
    l = Lesson(title=title, content=content, order=order)
    db.session.add(l)
    db.session.commit()
    flash("Lesson created.")
    return redirect(url_for("admin.dashboard"))

@admin_bp.post("/create-exercise")
@role_required(Role.ADMIN)
def create_exercise():
    lesson_id = int(request.form.get("lesson_id") or "0")
    title = (request.form.get("title") or "").strip()
    prompt = (request.form.get("prompt") or "").strip()
    tests_py = (request.form.get("tests_py") or "").strip()
    hint = (request.form.get("hint") or "").strip()
    level = (request.form.get("level") or "Beginner").strip()
    order = int(request.form.get("order") or "1")
    time_limit_ms = int(request.form.get("time_limit_ms") or "400")
    token_reward = int(request.form.get("token_reward") or "1")

    # rule toggles (unchecked checkbox -> missing)
    def _cb(name: str) -> bool:
        return (request.form.get(name) is not None)

    require_if = _cb("require_if")
    require_else = _cb("require_else")
    allow_elif = _cb("allow_elif")  # default on

    require_for = _cb("require_for")
    require_while = _cb("require_while")
    forbid_for = _cb("forbid_for")
    forbid_while = _cb("forbid_while")

    require_function = _cb("require_function")
    function_name = (request.form.get("function_name") or "").strip() or None

    require_print = _cb("require_print")
    forbid_print = _cb("forbid_print")
    require_input = _cb("require_input")

    # --- sanity checks / conflict resolution ---
    if require_function and not function_name:
        flash("If you require a function, you must set a function name.")
        return redirect(url_for("admin.dashboard"))

    # Mutually exclusive pairs (keep the 'require' intent if both selected)
    if require_print and forbid_print:
        forbid_print = False
        flash("Note: both 'require_print' and 'forbid_print' were selected; keeping require_print.")
    if require_for and forbid_for:
        forbid_for = False
        flash("Note: both 'require_for' and 'forbid_for' were selected; keeping require_for.")
    if require_while and forbid_while:
        forbid_while = False
        flash("Note: both 'require_while' and 'forbid_while' were selected; keeping require_while.")

    if not (lesson_id and title and prompt and tests_py):
        flash("Please fill required exercise fields.")
        return redirect(url_for("admin.dashboard"))

    ex = Exercise(
        lesson_id=lesson_id, title=title, prompt=prompt, tests_py=tests_py,
        hint=hint, level=level, order=order, time_limit_ms=time_limit_ms, token_reward=token_reward,
        require_if=require_if, require_else=require_else, allow_elif=allow_elif,
        require_for=require_for, require_while=require_while, forbid_for=forbid_for, forbid_while=forbid_while,
        require_function=require_function, function_name=function_name,
        require_print=require_print, forbid_print=forbid_print, require_input=require_input,
    )
    db.session.add(ex)
    db.session.commit()
    flash("Exercise created.")
    return redirect(url_for("admin.dashboard"))
