from flask import session, redirect, url_for

def login_required(func):

    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    return wrapper


def admin_required(func):

    def wrapper(*args, **kwargs):

        role = session.get("role")

        if role not in [0, 1]:
            return "Forbidden (Admin only)", 403

        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    return wrapper


def superadmin_required(func):

    def wrapper(*args, **kwargs):

        role = session.get("role")

        if role != 0:
            return "Forbidden (Super Admin only)", 403

        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    return wrapper