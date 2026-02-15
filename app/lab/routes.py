import os, uuid
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, send_from_directory, abort
from flask_login import current_user
from ..decorators import role_required
from ..extensions import db
from ..models import Role, LabProject, User

lab_bp = Blueprint("lab", __name__)

@lab_bp.get("/")
@role_required(Role.ADMIN, Role.TEACHER, Role.STUDENT)
def lab_home():
    if current_user.role == Role.STUDENT:
        projects = LabProject.query.filter_by(student_id=current_user.id).order_by(LabProject.created_at.desc()).all()
    elif current_user.role == Role.TEACHER:
        # teacher sees only their students' projects
        projects = (
            LabProject.query.join(User, LabProject.student_id==User.id)
            .filter(User.created_by_id==current_user.id)
            .order_by(LabProject.created_at.desc()).all()
        )
    else:
        projects = LabProject.query.order_by(LabProject.created_at.desc()).all()
    return render_template("lab.html", projects=projects)

@lab_bp.post("/upload")
@role_required(Role.STUDENT)
def upload():
    f = request.files.get("file")
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    if not f or not title:
        flash("Please provide title and file.")
        return redirect(url_for("lab.lab_home"))

    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in [".zip", ".py"]:
        flash("Upload .zip or .py only.")
        return redirect(url_for("lab.lab_home"))

    name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], name)
    f.save(path)

    p = LabProject(student_id=current_user.id, title=title, description=description, filename=name, is_published=True)
    db.session.add(p)
    db.session.commit()
    flash("Project uploaded.")
    return redirect(url_for("lab.lab_home"))

@lab_bp.get("/download/<filename>")
@role_required(Role.ADMIN, Role.TEACHER, Role.STUDENT)
def download(filename):
    # simple: anyone can download; for stricter security add checks.
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename, as_attachment=True)
