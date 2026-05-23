# ==========================================
# controllers/auth_controller.py
# ==========================================

from flask import flash, render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import session
from app.database.connection import get_db_connection
from werkzeug.security import check_password_hash, generate_password_hash
from app.controllers.audit_logs import create_audit_log


# ==========================================
# LOGIN PAGE
# ==========================================

def login():

    return render_template(
        "auth/login.html"
    )


# ==========================================
# LOGIN PROCESS
# ==========================================

def login_post():

    conn = None

    try:
        email = request.form.get("email")
        password = request.form.get("password")

        # Validasi input
        if not email or not password:
            return render_template(
                "auth/login.html",
                error="Email and password are required"
            )

        conn = get_db_connection()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            AND is_deleted = 0
            """,
            (email,)
        ).fetchone()

        # Cek user + password
        if not user or not check_password_hash(user["password"], password):

            return render_template(
                "auth/login.html",
                error="Email or password is incorrect"
            )

        # LOGIN SUCCESS → SIMPAN SESSION
        session["user_id"] = user["id"]
        session["name"] = user["name"]
        session["role"] = user["role"]
        
        create_audit_log(
            user_id=user["id"],
            action_type="Login",
            entity_type="User",
            entity_id=user["id"],
            detail=f"User {user['name']} logged in"
        )
        
        if user["role"] == 2:
            return redirect(url_for("incident_index"))
        
        return redirect(url_for("dashboard"))

    except Exception as e:
        print("ERROR LOGIN:", str(e))

        return render_template(
            "auth/login.html",
            error="A system error occurred"
        )

    finally:
        if conn:
            conn.close()
            
def change_password():
    return render_template("auth/change_password.html")
 
def change_password_update():
    conn = None

    try:
        conn = get_db_connection()

        user_id = session.get("user_id")

        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        # =========================
        # VALIDATION: EMPTY CHECK
        # =========================
        if not old_password or not new_password or not confirm_password:
            flash("All fields are required", "error")
            return redirect("/change-password")

        # =========================
        # VALIDATION: CONFIRM PASSWORD
        # =========================
        if new_password != confirm_password:
            flash("New password and confirmation do not match", "error")
            return redirect("/change-password")

        # =========================
        # GET USER DATA
        # =========================
        user = conn.execute("""
            SELECT password
            FROM users
            WHERE id = ?
        """, (user_id,)).fetchone()

        if not user:
            flash("User not found", "error")
            return redirect("/change-password")

        # =========================
        # CHECK OLD PASSWORD (HASHED)
        # =========================
        if not check_password_hash(user["password"], old_password):
            flash("Old password is incorrect", "error")
            return redirect("/change-password")

        # =========================
        # UPDATE PASSWORD (HASHED)
        # =========================
        hashed_password = generate_password_hash(new_password)

        conn.execute("""
            UPDATE users
            SET password = ?
            WHERE id = ?
        """, (hashed_password, user_id))
        
        create_audit_log(
            user_id=user_id,
            action_type="Change Password",
            entity_type="User",
            entity_id=user_id,
            detail=f"User {session.get('name')} changed their password"
        )

        conn.commit()

        flash("Password changed successfully", "success")

        return redirect("/dashboard")

    except Exception as e:
        print("CHANGE PASSWORD ERROR:", e)
        flash("An unexpected error occurred. Please try again later.", "error")
        return redirect("/change-password")

    finally:
        if conn:
            conn.close()
# ==========================================
# LOGOUT
# ==========================================

def logout():

    # HAPUS SESSION
    create_audit_log(
        session.get("user_id"),
        "Logout",
        "User",
        session.get("user_id"),
        "User logged out"
    )
    session.clear()    

    return redirect(
        url_for("login")
    )