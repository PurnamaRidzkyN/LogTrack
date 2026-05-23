# ==========================================
# controllers/incident_controller.py
# ==========================================

from flask import render_template

from app.database.connection import get_db_connection
from flask import request, session, flash, redirect, jsonify

from app.utils.time_helper import now_wib
from app.controllers.audit_logs import create_audit_log



# ==========================================
# INCIDENT LIST
# ==========================================
def incident_index():

    conn = None

    try:
        conn = get_db_connection()

        role = session.get("role")
        role = int(role) if role is not None else 2

        page = request.args.get("page", 1, type=int)
        q = request.args.get("q", "")
        start_date = request.args.get("start_date", "")
        end_date = request.args.get("end_date", "")

        limit = 10
        offset = (page - 1) * limit

        params = []

        # =========================
        # BASE QUERY + JOIN
        # =========================
        base_query = """
        FROM incidents i
        LEFT JOIN assets a ON i.asset_id = a.id
        LEFT JOIN incident_categories c ON i.incident_category_id = c.id
        LEFT JOIN users u ON i.user_id = u.id
        Left JOIN users h ON i.handled_by = h.id
        WHERE 1=1
        """

        # =========================
        # ROLE FILTER
        # =========================
        if role != 0:
            base_query += " AND i.is_deleted = 0"

        # =========================
        # SEARCH (SEMUA FIELD)
        # =========================
        if q:
            base_query += """
                AND (
                    i.severity_level LIKE ?
                    OR i.status LIKE ?
                    OR i.detail LIKE ?
                    OR a.asset_name LIKE ?
                    OR c.category_name LIKE ?
                    OR u.name LIKE ?
                    OR h.name LIKE ?
                )
            """
            params.extend([f"%{q}%"] * 7)

        # =========================
        # FILTER DATE (OPTIONAL)
        # =========================
        if start_date:
            base_query += " AND DATE(i.created_at) >= DATE(?)"
            params.append(start_date)

        if end_date:
            base_query += " AND DATE(i.created_at) <= DATE(?)"
            params.append(end_date)

        # =========================
        # COUNT
        # =========================
        total = conn.execute(
            f"SELECT COUNT(*) {base_query}",
            params
        ).fetchone()[0]

        # =========================
        # DATA
        # =========================
        incidents = conn.execute(
            f"""
            SELECT 
                i.*,
                a.asset_name,
                c.category_name,
                u.name AS reported_by,
                h.name AS handled_by_name
            {base_query}
            ORDER BY i.id DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset]
        ).fetchall()
        

        total_pages = (total + limit - 1) // limit

        return render_template(
            "incidents/index.html",
            incidents=incidents,
            page=page,
            total_pages=total_pages,
            q=q,
            start_date=start_date,
            end_date=end_date,
            role=role
        )

    except Exception as e:
        print("ERROR INCIDENT INDEX:", e)

        flash("Failed to retrieve incidents", "error")

        return render_template(
            "incidents/index.html",
            incidents=[],
            page=1,
            total_pages=1,
            q="",
            start_date="",
            end_date="",
            role=2
        )

    finally:
        if conn:
            conn.close()
            
def incident_edit(id):

    conn = None

    try:
        conn = get_db_connection()

        incident = conn.execute("""
            SELECT 
                i.*,
                a.asset_name,
                c.category_name,
                u.name AS reported_by,
                h.name AS handled_by_name
            FROM incidents i
            LEFT JOIN assets a ON i.asset_id = a.id
            LEFT JOIN incident_categories c ON i.incident_category_id = c.id
            left JOIN users u ON i.user_id = u.id
            left JOIN users h ON i.handled_by = h.id
            WHERE i.id = ?
        """, (id,)).fetchone()

        if not incident:
            flash("Incident not found", "error")
            return redirect("/incidents")

        return render_template(
            "incidents/edit.html",
            incident=incident
        )

    except Exception as e:
        print("ERROR INCIDENT EDIT:", e)
        flash("Failed to open incident edit", "error")
        return redirect("/incidents")

    finally:
        if conn:
            conn.close()
    
def incident_update(id):

    conn = None

    try:
        conn = get_db_connection()

        severity_level = request.form.get("severity_level")
        status = request.form.get("status")

        # =========================
        # VALIDATION
        # =========================
        allowed_severity = [
            "SEV-1",
            "SEV-2",
            "SEV-3"
        ]

        allowed_status = [
            "Open",
            "In Progress",
            "Resolved",
            "Closed"
        ]

        if severity_level not in allowed_severity:
            flash("Invalid severity", "error")
            return redirect(f"/incidents/{id}/edit")

        if status not in allowed_status:
            flash("Invalid status", "error")
            return redirect(f"/incidents/{id}/edit")
        
        handled_by = session.get("user_id")
        # =========================
        # UPDATE INCIDENT
        # =========================
        old_data = conn.execute("""
            SELECT severity_level, status
            FROM incidents
            WHERE id = ?
        """, (id,)).fetchone()
        
        changes = []
        
        if old_data["severity_level"] != severity_level:
            changes.append(
                f"severity_level: '{old_data['severity_level']}' -> '{severity_level}'"
            )

        if old_data["status"] != status:
            changes.append(
                f"status: '{old_data['status']}' -> '{status}'"
            )
        detail = ", ".join(changes)
        
        conn.execute("""
            UPDATE incidents
            SET
                handled_by = ?,
                severity_level = ?,
                status = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            handled_by,
            severity_level,
            status,
            now_wib(),
            id
        ))
        
        create_audit_log(
            handled_by,
            "UPDATE",
            "incident",
            id,
            f"Updated incident: {detail}"
        )

        conn.commit()

        flash("Incident successfully updated", "success")

    except Exception as e:
        print("ERROR INCIDENT UPDATE:", e)

        flash("Failed to update incident", "error")

    finally:
        if conn:
            conn.close()

    return redirect("/incidents")

def incident_detail(id):

    conn = None

    try:
        conn = get_db_connection()

        role = session.get("role")
        role = int(role) if role is not None else 2

        incident = conn.execute("""
            SELECT 
                i.*,
                a.asset_name,
                c.category_name,
                u.name AS user_name
            FROM incidents i
            LEFT JOIN assets a ON i.asset_id = a.id
            LEFT JOIN incident_categories c ON i.incident_category_id = c.id
            LEFT JOIN users u ON i.user_id = u.id
            WHERE i.id = ?
        """, (id,)).fetchone()

        if not incident:
            flash("Incident not found", "error")
            return redirect("/incidents")

        return render_template(
            "incidents/detail.html",
            incident=incident,
            role=role
        )

    except Exception as e:
        print("ERROR INCIDENT DETAIL:", e)
        flash("Failed to retrieve incident details", "error")
        return redirect("/incidents")

    finally:
        if conn:
            conn.close()
            
def incident_create():
    return render_template("incidents/create.html")
            
def incident_store():

    conn = None

    try:
        user_id = session.get("user_id")

        asset_id = request.form.get("asset_id")
        incident_category_id = request.form.get("incident_category_id")
        print("CATEGORY ID:", incident_category_id)
        detail = request.form.get("detail")

        conn = get_db_connection()

        # =========================
        # GET SEVERITY (SAFE)
        # =========================
        row = conn.execute("""
            SELECT default_severity
            FROM incident_categories
            WHERE id = ?
        """, (incident_category_id,)).fetchone()

        if not row:
            flash("Invalid category", "error")
            return redirect("/incidents/create")

        severity_level = row["default_severity"]

        # =========================
        # INSERT INCIDENT
        # =========================
        id = conn.execute("""
            INSERT INTO incidents (
                user_id,
                asset_id,
                incident_category_id,
                severity_level,
                detail,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            asset_id,
            incident_category_id,
            severity_level,
            detail,
            "Open",
            now_wib(),
            now_wib()
        ))
        id = id.lastrowid
        create_audit_log(
            user_id,
            "CREATE",
            "incident",
            id,
            f"Create new incident: {detail}"
        )
        conn.commit()

        flash("Incident successfully reported", "success")

    except Exception as e:
        print("ERROR STORE INCIDENT:", e)
        flash("Failed to create incident", "error")

    finally:
        if conn:
            conn.close()

    return redirect("/incidents")

def api_assets():
    q = request.args.get("q", "")

    conn = get_db_connection()

    data = conn.execute("""
        SELECT id, asset_name
        FROM assets
        WHERE (asset_name LIKE ? OR asset_code LIKE ?)
        AND is_deleted = 0
        LIMIT 10
    """, (f"%{q}%", f"%{q}%")).fetchall()

    return jsonify([dict(row) for row in data])

def api_categories():
    q = request.args.get("q", "")

    conn = get_db_connection()

    data = conn.execute("""
        SELECT id, category_name
        FROM incident_categories
        WHERE category_name LIKE ?
        AND is_deleted = 0
        LIMIT 10
    """, (f"%{q}%",)).fetchall()

    return jsonify([dict(row) for row in data])

# =========================
# SOFT DELETE
# =========================
def incident_delete(id):

    conn = None

    try:
        conn = get_db_connection()

        role = session.get("role")
        role = int(role) if role is not None else 2

        if role == 2:
            return "Forbidden", 403
        
        old_data = conn.execute("""
            SELECT is_deleted
            FROM incidents
            WHERE id = ?
        """, (id,)).fetchone()
        
        old_data = old_data["detail"]

        conn.execute("""
            UPDATE incidents
            SET is_deleted = 1,
                updated_at = ?
            WHERE id = ?
        """, (now_wib(), id))
        
        create_audit_log(
            session.get("user_id"),
            "DELETE",
            "incident",
            id,
            f"Soft delete incident: {old_data}"
        )
            
        conn.commit()

        flash("Incident successfully soft deleted", "warning")

    except Exception as e:
        print("ERROR SOFT DELETE INCIDENT:", e)
        flash("Failed to delete incident", "error")

    finally:
        if conn:
            conn.close()

    return redirect("/incidents")


# =========================
# RESTORE (SUPERADMIN ONLY)
# =========================
def incident_restore(id):

    conn = None

    try:
        conn = get_db_connection()

        role = session.get("role")
        role = int(role) if role is not None else 2

        if role != 0:
            return "Forbidden", 403

        old_data = conn.execute("""
            SELECT is_deleted
            FROM incidents
            WHERE id = ?
        """, (id,)).fetchone()
        
        old_data = old_data["detail"]
        
        conn.execute("""
            UPDATE incidents
            SET is_deleted = 0,
                updated_at = ?
            WHERE id = ?
        """, (now_wib(), id))
        
        create_audit_log(
            session.get("user_id"),
            "RESTORE",
            "incident",
            id,
            f"Restore incident: {old_data}"
        )

        conn.commit()

        flash("Incident successfully restored", "success")

    except Exception as e:
        print("ERROR RESTORE INCIDENT:", e)
        flash("Failed to restore incident", "error")

    finally:
        if conn:
            conn.close()

    return redirect("/incidents")


# =========================
# PERMANENT DELETE (SUPERADMIN ONLY)
# =========================
def incident_delete_permanent(id):

    conn = None

    try:
        conn = get_db_connection()

        role = session.get("role")
        role = int(role) if role is not None else 2

        if role != 0:
            return "Forbidden", 403
        
        old_data = conn.execute("""
            SELECT is_deleted
            FROM incidents
            WHERE id = ?
        """, (id,)).fetchone()
        
        old_data = old_data["detail"]

        conn.execute("""
            DELETE FROM incidents
            WHERE id = ?
        """, (id,))
        
        create_audit_log(
            session.get("user_id"),
            "DELETE_PERMANENT",
            "incident",
            id,
            f"Permanent delete incident: {old_data}"
        )

        conn.commit()

        flash("Incident permanently deleted", "error")

    except Exception as e:
        print("ERROR PERMANENT DELETE INCIDENT:", e)
        flash("Failed to permanently delete incident", "error")

    finally:
        if conn:
            conn.close()

    return redirect("/incidents")