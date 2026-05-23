
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
from app.utils.validators import validate_email, validate_string, validate_role
import logging
import traceback

logger = logging.getLogger(__name__)


def user_index():
    conn = None

    try:
        conn = get_db_connection()

        role = session.get("role")

        if role == 0:
            account = "Admin & User"
        elif role == 1:
            account = "User"

        q = request.args.get("q", "").strip()
        page = request.args.get("page", 1, type=int)

        # =========================
        # VALIDATION: PAGE NUMBER
        # =========================
        if page < 1:
            page = 1

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
        logger.error(f"USER INDEX ERROR: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        flash("An error occurred while loading users", "error")
        return render_template("users/index.html", users=[])

    finally:
        if conn:
            conn.close()
            
def user_create():
    return render_template("users/create.html")

def user_store():
    conn = None

    try:
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        role = request.form.get("role", "").strip()

        # =========================
        # VALIDATION: REQUIRED FIELDS
        # =========================
        if not name or not email or not role:
            flash("All fields are required", "error")
            return redirect("/users/create")

        # =========================
        # VALIDATION: NAME LENGTH
        # =========================
        if not validate_string(name, min_length=2, max_length=255):
            flash("Name must be between 2 and 255 characters", "error")
            return redirect("/users/create")

        # =========================
        # VALIDATION: EMAIL FORMAT
        # =========================
        if not validate_email(email):
            flash("Invalid email format", "error")
            return redirect("/users/create")

        # =========================
        # VALIDATION: ROLE
        # =========================
        if not validate_role(role):
            flash("Invalid role selected", "error")
            return redirect("/users/create")

        role = int(role)
        password = generate_password_hash(email)

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

        flash("User created successfully", "success")
        
    except sqlite3.IntegrityError as e:
        logger.error(f"USER STORE INTEGRITY ERROR: {str(e)}")
        if "email" in str(e).lower():
            flash("Email already exists", "error")
        else:
            flash("Data constraint violation", "error")

    except Exception as e:
        logger.error(f"USER STORE ERROR: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        flash("Failed to create user. Please try again.", "error")

    finally:
        if conn:
            conn.close()

    return redirect("/users")


def user_delete(id):
    conn = None

    try:
        # =========================
        # VALIDATION: ID FORMAT
        # =========================
        if not validate_string(str(id), min_length=1, max_length=10, allow_empty=False):
            flash("Invalid user ID", "error")
            return redirect("/users")

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

    except Exception as e:
        logger.error(f"USER DELETE ERROR: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        flash("An error occurred while deleting user", "error")

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
        
    except sqlite3.IntegrityError as e:
        logger.error(f"PERMANENT DELETE ACCOUNT IntegrityError: {e}")
        logger.error(traceback.format_exc())
        flash("Cannot permanently delete asset because it is referenced by other records.", "error")
        
    except Exception as e:
        logger.error(f"ERROR PERMANENT DELETE: {e}")
        logger.error(traceback.format_exc())
        flash("Failed to permanently delete asset", "error")

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
        logger.error(f"ERROR RESET PASSWORD: {e}")
        logger.error(traceback.format_exc())
        flash("Failed to reset password", "error")

    finally:
        if conn:
            conn.close()

    return redirect("/users")
