from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def role_required(*roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login_selector"))
            if current_user.role not in roles:
                flash("You don't have permission for this page.")
                return redirect(url_for("auth.login_selector"))
            if not current_user.subscription_ok():
                flash("Account inactive or subscription expired.")
                return redirect(url_for("auth.login_selector"))
            return fn(*args, **kwargs)
        return wrapper
    return deco
