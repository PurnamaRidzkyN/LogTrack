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
        print("ERROR INCIDENT CATEGORY INDEX:", e)

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
        category_name = request.form.get("category_name")
        default_severity = request.form.get("default_severity")

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

    except Exception as e:
        print("ERROR STORE INCIDENT CATEGORY:", e)
        flash("Failed to add incident category", "error")

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
        print("ERROR EDIT INCIDENT CATEGORY:", e)
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
        category_name = request.form.get("category_name")
        default_severity = request.form.get("default_severity")

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

    except Exception as e:
        print("ERROR UPDATE INCIDENT CATEGORY:", e)
        flash("Failed to update incident category", "error")

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
        print("ERROR SOFT DELETE:", e)
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
        print("ERROR RESTORE:", e)
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

        flash("Incident Category permanently deleted", "error")

    except Exception as e:
        print("ERROR PERMANENT DELETE:", e)
        flash("Failed to permanently delete incident category", "error")

    finally:
        if conn:
            conn.close()

    return redirect("/incident_categories")