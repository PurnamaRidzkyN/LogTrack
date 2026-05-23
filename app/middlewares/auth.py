from flask import session, redirect, url_for, flash
from functools import wraps

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            flash("You must login first", "error")
            return redirect(url_for("login"))

        return func(*args, **kwargs)

    return wrapper

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        role = session.get("role")

        if role not in [0, 1]:
            flash("Access denied: Admin only", "error")
            return redirect(url_for("dashboard"))

        return func(*args, **kwargs)

    return wrapper

def superadmin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        role = session.get("role")

        if role != 0:
            flash("Access denied: Super Admin only", "error")
            return redirect(url_for("dashboard"))

        return func(*args, **kwargs)

    return wrapper