
import sqlite3

from flask import (
    render_template,
    request,
    redirect,
    flash,
    session
)
from app.utils.time_helper import now_wib
from app.database.connection import get_db_connection
from app.controllers.audit_logs import create_audit_log
from werkzeug.security import generate_password_hash


def user_index():
    conn = None

    try:
        conn = get_db_connection()

        role = session.get("role")

        if role == 0:
            account = "Admin & User"
        elif role == 1:
            account = "User"

        q = request.args.get("q", "")
        page = request.args.get("page", 1, type=int)

        limit = 10
        offset = (page - 1) * limit

        query = """
            FROM users
            WHERE 1=1
        """
        params = []

        # =========================
        # SOFT DELETE FILTER
        # =========================
        if role == 1:  # admin
            query += " AND is_deleted = 0"
        params = []

        # =========================
        # ROLE FILTER
        # =========================
        if role == 1:
            query += " AND role = ?"
            params.append(2)

        # =========================
        # SEARCH
        # =========================
        if q:
            query += """
                AND (
                    name LIKE ?
                    OR email LIKE ?
                )
            """
            params.extend([f"%{q}%", f"%{q}%"])

        # =========================
        # COUNT
        # =========================
        total = conn.execute(
            f"SELECT COUNT(*) {query}",
            params
        ).fetchone()[0]
        
        # =========================
        # DATA
        # =========================
        users = conn.execute(
            f"""
            SELECT *
            {query}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset]
        ).fetchall()
        

        total_pages = (total + limit - 1) // limit

        return render_template(
            "users/index.html",
            users=users,
            q=q,
            account=account,
            page=page,
            total_pages=total_pages,
            role=role
        )

    except Exception as e:
        print("ERROR USER INDEX:", e)
        return render_template("users/index.html", users=[])

    finally:
        if conn:
            conn.close()
            
def user_create():
    return render_template("users/create.html")

def user_store():
    conn = None

    try:
        name = request.form.get("name")
        email = request.form.get("email")
        password = generate_password_hash(email)
        role = request.form.get("role")  

        conn = get_db_connection()

        cursor = conn.execute("""
            INSERT INTO users (
                name,
                email,
                password,
                role,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (name, email, password, role, now_wib()))

        user_id = cursor.lastrowid

        create_audit_log(
            session.get("user_id"),
            "CREATE",
            "user",
            user_id,
            f"Create user {name}"
        )

        conn.commit()

        flash("User created", "success")
        
    except sqlite3.IntegrityError as e:

        print("ERROR USER STORE:", e)

        if "email" in str(e).lower():
            flash("Email already exists", "error")
        else:
            flash("Data constraint violation", "error")

    except Exception as e:
        print("ERROR USER STORE:", e)
        flash("Failed create user", "error")

    finally:
        if conn:
            conn.close()

    return redirect("/users")


def user_delete(id):
    conn = None

    try:
        conn = get_db_connection()

        current_user_id = session.get("user_id")
        current_role = session.get("role")

        # =========================
        # GET TARGET USER
        # =========================
        old_data = conn.execute("""
            SELECT id, name, role
            FROM users
            WHERE id = ?
        """, (id,)).fetchone()

        if not old_data:
            flash("User not found", "error")
            return redirect("/users")

        # =========================
        # PROTECTION RULES
        # =========================

        # ❌ tidak boleh hapus diri sendiri
        if int(id) == int(current_user_id):
            flash("You cannot delete your own account", "error")
            return redirect("/users")

        # ❌ superadmin tidak boleh dihapus
        if old_data["role"] == 0:
            flash("Super Admin cannot be deleted", "error")
            return redirect("/users")

        # =========================
        # ROLE LABEL
        # =========================
        old_name = old_data["name"]
        old_role = (
            "superadmin" if old_data["role"] == 0
            else "admin" if old_data["role"] == 1
            else "user"
        )

        # =========================
        # SOFT DELETE
        # =========================
        conn.execute("""
            UPDATE users
            SET is_deleted = 1
            WHERE id = ?
        """, (id,))

        # =========================
        # AUDIT LOG
        # =========================
        create_audit_log(
            session.get("user_id"),
            "DELETE",
            "user",
            id,
            f"Soft delete {old_role} {old_name}"
        )

        conn.commit()

        flash("User deleted successfully", "success")

    finally:
        if conn:
            conn.close()

    return redirect("/users")

def user_restore(id):
    conn = None

    try:
        conn = get_db_connection()
        
        old_data = conn.execute("""
            SELECT name, role, is_deleted
            FROM users
            WHERE id = ?
            """, (id,)).fetchone()
        
        old_name = old_data["name"] if old_data else "Unknown"
        old_role = (
            "superadmin" if old_data["role"] == 0
            else "admin" if old_data["role"] == 1
            else "user" if old_data["role"] == 2
            else "Unknown"
        )

        conn.execute("""
            UPDATE users
            SET is_deleted = 0
            WHERE id = ?
        """, (id,))

        create_audit_log(
            session.get("user_id"),
            "RESTORE",
            "user",
            id,
            f"Restore {old_role} {old_name}"
        )

        conn.commit()

    finally:
        if conn:
            conn.close()

    return redirect("/users")

def user_force_delete(id):
    conn = None

    try:
        conn = get_db_connection()
        
        old_data = conn.execute("""
            SELECT name, role
            FROM users
            WHERE id = ?
        """, (id,)).fetchone()
        
        old_name = old_data["name"] if old_data else "Unknown"
        old_role = (
            "superadmin" if old_data["role"] == 0
            else "admin" if old_data["role"] == 1
            else "user" if old_data["role"] == 2
            else "Unknown"
        )

        conn.execute("""
            DELETE FROM users
            WHERE id = ?
        """, (id,))

        create_audit_log(
            session.get("user_id"),
            "DELETE",
            "user",
            id,
            f"Permanent delete ({old_role}) {old_name}"
        )

        conn.commit()

    finally:
        if conn:
            conn.close()

    return redirect("/users")

def user_reset_password(id):
    conn = None

    try:
        conn = get_db_connection()

        user = conn.execute("""
            SELECT email, name, role
            FROM users
            WHERE id = ?
        """, (id,)).fetchone()
        
        old_role = (
            "superadmin" if user["role"] == 0
            else "admin" if user["role"] == 1
            else "user" if user["role"] == 2
            else "Unknown"
        )
        if not user:
            flash("User not found", "error")
            return redirect("/users")

        new_password = generate_password_hash(user["email"])

        conn.execute("""
            UPDATE users
            SET password = ?
            WHERE id = ?
        """, (new_password, id))

        create_audit_log(
            session.get("user_id"),
            "UPDATE",
            "user",
            id,
            f"Reset password {old_role} {user['name']}"
        )

        conn.commit()

        flash("Password successfully reset", "success")

    except Exception as e:
        print("ERROR RESET PASSWORD:", e)
        flash("Failed to reset password", "error")

    finally:
        if conn:
            conn.close()

    return redirect("/users")
