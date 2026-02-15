from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import current_user
from ..decorators import role_required
from ..extensions import db
from ..models import Role, Lesson, Exercise, Submission, Progress
from ..services.gating import can_open_exercise, get_progress, progress_stats
from ..services.tokens import spend_token
from ..services.grader import grade_python
from ..services.code_checker import check_code
from ..services.runner import run_python

student_bp = Blueprint("student", __name__)

@student_bp.get("/")
@role_required(Role.STUDENT)
def dashboard():
    lessons = Lesson.query.order_by(Lesson.order.asc()).all()
    prog = get_progress(current_user.id)
    passed_count, total = progress_stats(current_user.id)
    progress_pct = 0 if total == 0 else int((passed_count / total) * 100)
    return render_template(
        "student_dashboard.html",
        lessons=lessons,
        prog=prog,
        total=total,
        passed=passed_count,
        progress_pct=progress_pct,
    )

@student_bp.get("/lesson/<int:lesson_id>")
@role_required(Role.STUDENT)
def lesson_view(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    exercises = Exercise.query.filter_by(lesson_id=lesson_id).order_by(Exercise.order.asc()).all()
    return render_template("lesson.html", lesson=lesson, exercises=exercises)

@student_bp.get("/exercise/<int:exercise_id>")
@role_required(Role.STUDENT)
def exercise_view(exercise_id):
    ex = Exercise.query.get_or_404(exercise_id)
    if not can_open_exercise(current_user.id, ex.id):
        flash("This exercise is locked. Pass the previous one first.")
        return redirect(url_for("student.dashboard"))
    last = Submission.query.filter_by(student_id=current_user.id, exercise_id=ex.id).order_by(Submission.id.desc()).first()
    return render_template("exercise.html", ex=ex, last=last, show_hint=False)

@student_bp.post("/exercise/<int:exercise_id>/hint")
@role_required(Role.STUDENT)
def hint(exercise_id):
    ex = Exercise.query.get_or_404(exercise_id)
    if not spend_token(current_user, 1):
        flash("Not enough tokens.")
        return redirect(url_for("student.exercise_view", exercise_id=ex.id))
    last = Submission.query.filter_by(student_id=current_user.id, exercise_id=ex.id).order_by(Submission.id.desc()).first()
    return render_template("exercise.html", ex=ex, last=last, show_hint=True)

# ✅ Terminal Run endpoint (supports input via stdin_text)
@student_bp.post("/exercise/<int:exercise_id>/run")
@role_required(Role.STUDENT)
def run_code(exercise_id):
    ex = Exercise.query.get_or_404(exercise_id)
    if not can_open_exercise(current_user.id, ex.id):
        return jsonify({"status": "LOCKED", "stdout": "", "stderr": "Locked"}), 403

    code = request.form.get("code_py") or ""
    stdin_text = request.form.get("stdin_text") or ""

    result = run_python(code, stdin_text)
    return jsonify(result)

@student_bp.post("/exercise/<int:exercise_id>/submit")
@role_required(Role.STUDENT)
def submit(exercise_id):
    ex = Exercise.query.get_or_404(exercise_id)
    if not can_open_exercise(current_user.id, ex.id):
        flash("Locked.")
        return redirect(url_for("student.exercise_view", exercise_id=ex.id))

    code = request.form.get("code_py") or ""
    sub = Submission(student_id=current_user.id, exercise_id=ex.id, code_py=code, status="PENDING")
    db.session.add(sub)
    db.session.commit()

    # 1) Check structural rules before running pytest (fast + clearer feedback)
    try:
        rule_errors = check_code(code, ex)
    except Exception as e:
        rule_errors = [f"Code rule check failed: {e}"]

    if rule_errors:
        sub.status = "FAILED"
        sub.runtime_ms = 0
        sub.output = "CODE RULES FAILED:\n" + "\n".join([f"- {m}" for m in rule_errors])
        db.session.commit()
        flash("Code rules not satisfied. Fix the issues and try again.")
        return redirect(url_for("student.exercise_view", exercise_id=ex.id))

    # 2) Then run tests in the grader
    result = grade_python(code, ex.tests_py)
    sub.runtime_ms = result.get("runtime_ms")
    sub.output = result.get("output") or ""

    if result["status"] == "PASSED":
        sub.status = "WAITING_APPROVAL"
        sub.output += "\n\n✅ Tests passed. Waiting for teacher approval."
    elif result["status"] == "FAILED":
        sub.status = "FAILED"
    else:
        sub.status = "ERROR"

    db.session.commit()

    # ✅ Redirect to dashboard + congrats on success
    if sub.status == "WAITING_APPROVAL":
        flash("🎉 Correct! Tests passed ✅. Waiting for teacher approval.")
        return redirect(url_for("student.dashboard"))

    flash("Not passed yet. Check output.")
    return redirect(url_for("student.exercise_view", exercise_id=ex.id))
