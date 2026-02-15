from flask import Blueprint, render_template, redirect, url_for, request, abort
from flask_login import current_user
from ..decorators import role_required
from ..extensions import db
from ..models import Role, User, Message

chat_bp = Blueprint("chat", __name__)

def _allowed_chat(other: User) -> bool:
    if current_user.role == Role.TEACHER and other.role == Role.STUDENT and other.created_by_id == current_user.id:
        return True
    if current_user.role == Role.STUDENT and other.role == Role.TEACHER and current_user.created_by_id == other.id:
        return True
    if current_user.role == Role.ADMIN:
        return True
    return False

@chat_bp.get("/with/<int:user_id>")
@role_required(Role.ADMIN, Role.TEACHER, Role.STUDENT)
def chat_with(user_id):
    other = User.query.get_or_404(user_id)
    if not _allowed_chat(other):
        abort(403)

    msgs = Message.query.filter(
        ((Message.sender_id==current_user.id) & (Message.receiver_id==other.id)) |
        ((Message.sender_id==other.id) & (Message.receiver_id==current_user.id))
    ).order_by(Message.created_at.asc()).all()

    return render_template("chat.html", other=other, msgs=msgs)

@chat_bp.post("/with/<int:user_id>")
@role_required(Role.ADMIN, Role.TEACHER, Role.STUDENT)
def send(user_id):
    other = User.query.get_or_404(user_id)
    if not _allowed_chat(other):
        abort(403)
    text = (request.form.get("text") or "").strip()
    if text:
        m = Message(sender_id=current_user.id, receiver_id=other.id, text=text)
        db.session.add(m)
        db.session.commit()
    return redirect(url_for("chat.chat_with", user_id=other.id))
