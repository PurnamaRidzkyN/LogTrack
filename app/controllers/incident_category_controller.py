# ==========================================
# controllers/incident_category_controller.py
# ==========================================

from flask import (
    render_template,
    request,
    redirect,
    flash,
    session
)
from app.controllers.audit_logs import create_audit_log
from app.database.connection import get_db_connection
from app.utils.time_helper import now_wib
import sqlite3
import logging
import traceback

logger = logging.getLogger(__name__)
from app.utils.validators import validate_string, validate_severity
from app.utils.error_handler import handle_db_error


# ==========================================
# INDEX
# ==========================================
def incident_category_index():

    conn = None

    try:
        conn = get_db_connection()

        role = session.get("role")
        role = int(role) if role is not None else 2

        page = request.args.get("page", 1, type=int)
        q = request.args.get("q", "")

        limit = 10
        offset = (page - 1) * limit
        
        if role == 0:
            base_query = "FROM incident_categories WHERE 1=1"
        else:
            base_query = "FROM incident_categories WHERE is_deleted = 0"
        params = []

        if q:
            base_query += " AND (category_name LIKE ? OR default_severity LIKE ?)"
            params.extend([f"%{q}%", f"%{q}%"])

        total = conn.execute(
            f"SELECT COUNT(*) {base_query}",
            params
        ).fetchone()[0]

        incident_categories = conn.execute(
            f"""
            SELECT *
            {base_query}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset]
        ).fetchall()

        total_pages = (total + limit - 1) // limit
        

        return render_template(
            "incident_categories/index.html",
            incident_categories=incident_categories,
            page=page,
            total_pages=total_pages,
            q=q,
            role=role
        )

    except Exception as e:
        logger.error(f"ERROR INCIDENT CATEGORY INDEX: {e}")
        logger.error(traceback.format_exc())
        flash("Failed to retrieve incident categories", "error")

        return render_template(
            "incident_categories/index.html",
            incident_categories=[],
            page=1,
            total_pages=1,
            q="",
            role=2
        )

    finally:
        if conn:
            conn.close()
# ==========================================
# CREATE PAGE
# ==========================================

def incident_category_create():
    return render_template("incident_categories/create.html")


# ==========================================
# STORE
# ==========================================

def incident_category_store():

    conn = None

    try:
        category_name = request.form.get("category_name", "").strip()
        default_severity = request.form.get("default_severity", "").strip()

        # Validation
        if not validate_string(category_name, min_length=1, max_length=255):
            flash("Category name is required (1-255 chars)", "error")
            return redirect("/incident_categories/create")

        if not validate_severity(default_severity):
            flash("Invalid default severity", "error")
            return redirect("/incident_categories/create")

        conn = get_db_connection()

        cursor = conn.execute("""
            INSERT INTO incident_categories (
                category_name,
                default_severity,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?)
        """, (category_name, default_severity, now_wib(), now_wib()))
        
        category_id = cursor.lastrowid
        create_audit_log(
            session.get("user_id"),
            "CREATE",
            "incident_category",
            category_id,
            f"Create new incident category: {category_name}")

        conn.commit()

        flash("Incident Category successfully added", "success")

    except sqlite3.IntegrityError as e:
        logger.error(f"INCIDENT CATEGORY STORE IntegrityError: {e}")
        flash("Data constraint violation", "error")
    except Exception as e:
        resp = handle_db_error(e, user_id=session.get("user_id"), entity_type="incident_category")
        flash(resp.get('error'), 'error')

    finally:
        if conn:
            conn.close()

    return redirect("/incident_categories")


# ==========================================
# EDIT PAGE
# ==========================================
def incident_category_edit(id):

    conn = None

    try:
        conn = get_db_connection()

        incident_category = conn.execute("""
            SELECT *
            FROM incident_categories
            WHERE id = ?
        """, (id,)).fetchone()

        if not incident_category:
            flash("Incident Category not found", "error")
            return redirect("/incident_categories")

        return render_template("incident_categories/edit.html", incident_category=incident_category)

    except Exception as e:
        logger.error(f"ERROR EDIT INCIDENT CATEGORY: {e}")
        logger.error(traceback.format_exc())
        flash("Failed to open incident category data", "error")
        return redirect("/incident_categories")

    finally:
        if conn:
            conn.close()

# ==========================================
# UPDATE
# ==========================================
def incident_category_update(id):

    conn = None

    try:
        category_name = request.form.get("category_name", "").strip()
        default_severity = request.form.get("default_severity", "").strip()

        # Validation
        if not validate_string(category_name, min_length=1, max_length=255):
            flash("Category name is required (1-255 chars)", "error")
            return redirect(f"/incident_categories/{id}/edit")

        if not validate_severity(default_severity):
            flash("Invalid default severity", "error")
            return redirect(f"/incident_categories/{id}/edit")

        conn = get_db_connection()

        # OLD DATA
        old_data = conn.execute("""
            SELECT category_name, default_severity
            FROM incident_categories
            WHERE id = ?
        """, (id,)).fetchone()

        changes = []
        if category_name != old_data[0]:
            changes.append(f"category_name: '{old_data[0]}' -> '{category_name}'")
        if default_severity != old_data[1]:
            changes.append(f"default_severity: '{old_data[1]}' -> '{default_severity}'")
            
        detail = ", ".join(changes)
        
        conn.execute("""
            UPDATE incident_categories
            SET
                category_name = ?,
                default_severity = ?,
                updated_at = ?
            WHERE id = ?
        """, ( category_name, default_severity, now_wib(), id))
        
        
        create_audit_log(
            session.get("user_id"),
            "UPDATE",
            "incident_category",
            id,
            f"Update category: {detail}")

        conn.commit()

        flash("Incident Category successfully updated", "success")

    except sqlite3.IntegrityError as e:
        logger.error(f"INCIDENT CATEGORY UPDATE IntegrityError: {e}")
        flash("Data constraint violation", "error")
    except Exception as e:
        resp = handle_db_error(e, user_id=session.get("user_id"), entity_type="incident_category")
        flash(resp.get('error'), 'error')

    finally:
        if conn:
            conn.close()

    return redirect("/incident_categories")


# ==========================================
# SOFT DELETE
# ==========================================

def incident_category_delete(id):

    conn = None

    try:
        conn = get_db_connection()
        
        old_data = conn.execute("""
            SELECT category_name
            FROM incident_categories
            WHERE id = ?
        """, (id,)).fetchone()
        
        old_name = old_data["category_name"]

        conn.execute("""
            UPDATE incident_categories
            SET is_deleted = 1,
                updated_at = ?
            WHERE id = ?
        """, (now_wib(), id))

        create_audit_log(
            session.get("user_id"),
            "DELETE",
            "incident_category",
            id,
            f"Soft delete category: {old_name}")
        conn.commit()

        flash("Incident Category successfully deleted", "warning")

    except Exception as e:
        logger.error(f"ERROR SOFT DELETE: {e}")
        logger.error(traceback.format_exc())
        flash("Failed to delete incident category", "error")

    finally:
        if conn:
            conn.close()

    return redirect("/incident_categories")


# ==========================================
# RESTORE
# ==========================================
def incident_category_restore(id):

    conn = None

    try:
        role = session.get("role")

        if role != 0:
            return "Forbidden", 403

        conn = get_db_connection()
        
        old_data = conn.execute("""
            SELECT category_name
            FROM incident_categories
            WHERE id = ?
        """, (id,)).fetchone()
        
        old_name = old_data["category_name"]

        conn.execute("""
            UPDATE incident_categories
            SET is_deleted = 0,
                updated_at = ?
            WHERE id = ?
        """, (now_wib(), id))

        create_audit_log(
            session.get("user_id"),
            "RESTORE",
            "incident_category",
            id,
            f"Restore category: {old_name}")

        conn.commit()

        flash("Incident Category successfully restored", "success")

    except Exception as e:
        logger.error(f"ERROR RESTORE: {e}")
        logger.error(traceback.format_exc())
        flash("Failed to restore incident category", "error")

    finally:
        if conn:
            conn.close()

    return redirect("/incident_categories")

# ==========================================
# PERMANENT DELETE
# ==========================================
def incident_category_delete_permanent(id):

    conn = None

    try:
        role = session.get("role")

        if role != 0:
            return "Forbidden", 403

        conn = get_db_connection()
        
        old_data = conn.execute("""
            SELECT category_name
            FROM incident_categories
            WHERE id = ?
        """, (id,)).fetchone()
        
        old_name = old_data["category_name"]

        conn.execute("""
            DELETE FROM incident_categories
            WHERE id = ?
        """, (id,))
        
        create_audit_log(
            session.get("user_id"),
            "DELETE",
            "incident_category",
            id,
            f"Permanent delete category: {old_name}")


        conn.commit()

        flash("Incident Category permanently deleted", "success")

    except sqlite3.IntegrityError as e:
        logger.error(f"PERMANENT DELETE CATEGORY IntegrityError: {e}")
        logger.error(traceback.format_exc())
        flash("Cannot permanently delete incident category because it is referenced by other records.", "error")

    except Exception as e:
        logger.error(f"ERROR PERMANENT DELETE: {e}")
        logger.error(traceback.format_exc())
        flash("Failed to permanently delete incident category", "error")

    finally:
        if conn:
            conn.close()

    return redirect("/incident_categories")