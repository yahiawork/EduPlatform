import secrets
import time

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from ..extensions import limiter
from ..models import User, Role
from ..extensions import db
from ..services.emailer import send_email

auth_bp = Blueprint("auth", __name__)

@auth_bp.get("/login")
def login_selector():
    return render_template("auth_login_selector.html")

@auth_bp.get("/login/<role>")
def login_role(role):
    role = (role or "").lower()
    if role not in ["admin", "teacher", "student"]:
        return redirect(url_for("auth.login_selector"))
    return render_template("auth_login_role.html", role=role)

@auth_bp.post("/login/<role>")
@limiter.limit("10 per minute")
def login_role_post(role):
    role = (role or "").lower()
    if role not in ["admin", "teacher", "student"]:
        return redirect(url_for("auth.login_selector"))

    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        flash("Invalid credentials.")
        return redirect(url_for("auth.login_role", role=role))

    # ✅ enforce role matches selected login
    if user.role != role:
        flash(f"This account is not a {role.upper()} account.")
        return redirect(url_for("auth.login_role", role=role))

    if not user.subscription_ok():
        flash("Account inactive or subscription expired.")
        return redirect(url_for("auth.login_role", role=role))

    # Admin OTP (2-step verification)
    if user.role == Role.ADMIN:
        email = (request.form.get("email") or "").strip().lower()
        if not email:
            flash("Admin email is required.")
            return redirect(url_for("auth.login_role", role=role))

        # First-time setup: save admin email if it's not set yet.
        if not getattr(user, "email", None):
            # prevent duplicates
            if User.query.filter(User.email == email, User.id != user.id).first():
                flash("This email is already used by another account.")
                return redirect(url_for("auth.login_role", role=role))
            user.email = email
            db.session.commit()

        if (user.email or "").lower() != email:
            flash("Email does not match the admin account.")
            return redirect(url_for("auth.login_role", role=role))

        code = f"{secrets.randbelow(1_000_000):06d}"
        ttl = int(current_app.config.get("ADMIN_OTP_TTL_SEC", 300))
        session["admin_otp_user_id"] = user.id
        session["admin_otp_hash"] = generate_password_hash(code)
        session["admin_otp_exp"] = int(time.time()) + ttl

        expires_text = f"{ttl//60} minutes" if ttl >= 60 else f"{ttl} seconds"

        html = render_template(
            "emails/admin_otp.html",
            subject="EduPlatform Admin Login Code",
            preheader="Your admin login code is ready.",
            brand="EduPlatform",
            header_right="Security check",
            title="Admin login code",
            subtitle="Use the code below to finish signing in.",
            code=code,
            expires_text=expires_text,
            button_url=None,
            button_text="Continue",
            footer="If you did not attempt to sign in, you can ignore this message.",
            legal="© EduPlatform",
        )

        err = send_email(
            to_email=user.email,
            subject="EduPlatform Admin Login Code",
            body=(
                "Your EduPlatform admin login code is:\n\n"
                f"{code}\n\n"
                f"This code expires in {expires_text}."
            ),
            html=html,
        )
        if err:
            flash(err)
            return redirect(url_for("auth.login_role", role=role))

        flash("A verification code was sent to your email.")
        return redirect(url_for("auth.admin_otp"))

    login_user(user)
    return redirect(url_for("core.index"))


@auth_bp.get("/admin-otp")
@limiter.limit("10 per minute")
def admin_otp():
    if not session.get("admin_otp_user_id"):
        return redirect(url_for("auth.login_role", role="admin"))
    return render_template("auth_admin_otp.html")


@auth_bp.post("/admin-otp")
@limiter.limit("10 per minute")
def admin_otp_post():
    user_id = session.get("admin_otp_user_id")
    otp_hash = session.get("admin_otp_hash")
    exp = int(session.get("admin_otp_exp") or 0)
    code = (request.form.get("code") or "").strip()

    if not user_id or not otp_hash:
        flash("Session expired. Please login again.")
        return redirect(url_for("auth.login_role", role="admin"))
    if int(time.time()) > exp:
        session.pop("admin_otp_user_id", None)
        session.pop("admin_otp_hash", None)
        session.pop("admin_otp_exp", None)
        flash("Verification code expired. Please login again.")
        return redirect(url_for("auth.login_role", role="admin"))

    if not (len(code) == 6 and code.isdigit() and check_password_hash(otp_hash, code)):
        flash("Invalid verification code.")
        return redirect(url_for("auth.admin_otp"))

    user = User.query.get(int(user_id))
    if not user or user.role != Role.ADMIN:
        flash("Invalid session. Please login again.")
        return redirect(url_for("auth.login_role", role="admin"))

    # clear OTP session
    session.pop("admin_otp_user_id", None)
    session.pop("admin_otp_hash", None)
    session.pop("admin_otp_exp", None)

    login_user(user)
    return redirect(url_for("core.index"))

@auth_bp.get("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login_selector"))
