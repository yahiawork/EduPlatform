from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import current_user
from ..decorators import role_required
from ..extensions import db
from ..models import Role, User, Submission, Exercise
from ..services.gating import mark_passed
from ..services.tokens import add_tokens

teacher_bp = Blueprint("teacher", __name__)

@teacher_bp.get("/")
@role_required(Role.TEACHER)
def dashboard():
    my_students = User.query.filter_by(role=Role.STUDENT, created_by_id=current_user.id).order_by(User.created_at.desc()).all()
    waiting_count = (
        Submission.query.join(User, Submission.student_id==User.id)
        .filter(User.created_by_id==current_user.id, Submission.status=="WAITING_APPROVAL")
        .count()
    )
    recent = (
        Submission.query.join(User, Submission.student_id==User.id)
        .filter(User.created_by_id==current_user.id)
        .order_by(Submission.created_at.desc())
        .limit(20).all()
    )
    return render_template("teacher_dashboard.html", my_students=my_students, recent=recent, waiting_count=waiting_count)

@teacher_bp.post("/create-student")
@role_required(Role.TEACHER)
def create_student():
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    if not username or not password:
        flash("Please fill username and password.")
        return redirect(url_for("teacher.dashboard"))
    if User.query.filter_by(username=username).first():
        flash("Username already exists.")
        return redirect(url_for("teacher.dashboard"))

    s = User(username=username, role=Role.STUDENT, created_by_id=current_user.id)
    s.set_password(password)
    s.extend_month()
    db.session.add(s)
    db.session.commit()
    flash("Student created and linked to you.")
    return redirect(url_for("teacher.dashboard"))

@teacher_bp.get("/reviews")
@role_required(Role.TEACHER)
def reviews():
    waiting = (
        Submission.query.join(User, Submission.student_id==User.id)
        .filter(User.created_by_id==current_user.id, Submission.status=="WAITING_APPROVAL")
        .order_by(Submission.created_at.desc()).all()
    )
    return render_template("teacher_reviews.html", waiting=waiting)

@teacher_bp.post("/reviews/<int:sub_id>/approve")
@role_required(Role.TEACHER)
def approve(sub_id):
    sub = Submission.query.get_or_404(sub_id)
    student = User.query.filter_by(id=sub.student_id, role=Role.STUDENT, created_by_id=current_user.id).first()
    if not student:
        abort(403)

    note = (request.form.get("note") or "").strip()
    sub.status = "APPROVED"
    sub.reviewed_by_id = current_user.id
    sub.reviewed_at = datetime.utcnow()
    sub.review_note = note
    db.session.commit()

    ex = Exercise.query.get(sub.exercise_id)
    mark_passed(student.id, ex.id)
    add_tokens(student, ex.token_reward)

    flash(f"Approved ✅ (+{ex.token_reward} tokens).")
    return redirect(url_for("teacher.reviews"))

@teacher_bp.post("/reviews/<int:sub_id>/reject")
@role_required(Role.TEACHER)
def reject(sub_id):
    sub = Submission.query.get_or_404(sub_id)
    student = User.query.filter_by(id=sub.student_id, role=Role.STUDENT, created_by_id=current_user.id).first()
    if not student:
        abort(403)

    note = (request.form.get("note") or "").strip()
    sub.status = "REJECTED"
    sub.reviewed_by_id = current_user.id
    sub.reviewed_at = datetime.utcnow()
    sub.review_note = note
    db.session.commit()

    flash("Rejected ❌.")
    return redirect(url_for("teacher.reviews"))
