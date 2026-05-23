
from datetime import datetime

from flask import (
    render_template,
    request,
    redirect,
    flash,
    session
)
from app.utils.time_helper import now_wib
from app.database.connection import get_db_connection


def audit_log_index():

    conn = None

    try:
        conn = get_db_connection()

        page = request.args.get("page", 1, type=int)
        q = request.args.get("q", "")
        start_date = request.args.get("start_date", "")
        end_date = request.args.get("end_date", "")

        limit = 10
        offset = (page - 1) * limit

        params = []

        # =========================
        # BASE QUERY
        # =========================
        base_query = """
        FROM audit_logs a
        LEFT JOIN users u ON a.user_id = u.id
        WHERE 1=1
        """

        # =========================
        # SEARCH
        # =========================
        if q:
            base_query += """
                AND (
                    a.action_type LIKE ?
                    OR a.entity_type LIKE ?
                    OR a.detail LIKE ?
                )
            """

            params.extend([f"%{q}%"] * 3)
            
        if start_date:
            base_query += " AND DATE(a.created_at) >= DATE(?)"
            params.append(start_date)

        if end_date:
            base_query += " AND DATE(a.created_at) <= DATE(?)"
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
        rows = conn.execute(
            f"""
            SELECT
                a.*,
                u.name AS user_name
            {base_query}
            ORDER BY a.id DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset]
        ).fetchall()
        
        logs = []

        for row in rows:
            row = dict(row)

            # format created_at
            if row.get("created_at"):
                dt = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S")
                row["created_at"] = dt.strftime("%d %b %Y • %H:%M")

            logs.append(row)
        total_pages = (total + limit - 1) // limit

        return render_template(
            "audit_logs/index.html",
            logs=logs,
            page=page,
            total_pages=total_pages,
            start_date=start_date,
            end_date=end_date,
            q=q,
            role = session.get("role")
        )

    except Exception as e:
        print("ERROR AUDIT LOG INDEX:", e)

        flash("Failed to retrieve audit logs", "error")

        return render_template(
            "audit_logs/index.html",
            logs=[],
            page=1,
            total_pages=1,
            q="",
            role = session.get("role")
            
        )

    finally:
        if conn:
            conn.close()
            

def create_audit_log(
    user_id,
    action_type,
    entity_type,
    entity_id,
    detail
):

    conn = None

    try:
        conn = get_db_connection()

        conn.execute("""
            INSERT INTO audit_logs (
                user_id,
                action_type,
                entity_type,
                entity_id,
                detail,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            action_type,
            entity_type,
            entity_id,
            detail,
            now_wib()
        ))

        conn.commit()

    except Exception as e:
        print("ERROR CREATE AUDIT LOG:", e)

    finally:
        if conn:
            conn.close()