# ==========================================
# controllers/asset_controller.py
# ==========================================

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
import sqlite3
import logging
import traceback

logger = logging.getLogger(__name__)
from app.utils.validators import validate_string, validate_asset_status
from app.utils.error_handler import handle_db_error

# ==========================================
# INDEX
# ==========================================
def asset_index():

    conn = None

    try:
        conn = get_db_connection()

        role = session.get("role")
        role = int(role) if role is not None else 2

        page = request.args.get("page", 1, type=int)
        q = request.args.get("q", "")

        limit = 10
        offset = (page - 1) * limit

        params = []

        # =========================
        # ROLE BASED FILTER
        # =========================
        if role == 0:
            base_query = "FROM assets WHERE 1=1"
        else:
            base_query = "FROM assets WHERE is_deleted = 0"

        # =========================
        # SEARCH
        # =========================
        if q:
            base_query += " AND (asset_code LIKE ? OR asset_name LIKE ? OR status LIKE ?)"
            params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])

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
        assets = conn.execute(
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
            "assets/index.html",
            assets=assets,
            page=page,
            total_pages=total_pages,
            q=q,
            role=role
        )

    except Exception as e:
        logger.error(f"ERROR ASSET INDEX: {e}")
        logger.error(traceback.format_exc())
        flash("Failed to retrieve assets", "error")

        return render_template(
            "assets/index.html",
            assets=[],
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

def asset_create():
    return render_template("assets/create.html")


# ==========================================
# STORE
# ==========================================

def asset_store():

    conn = None

    try:
        asset_code = request.form.get("asset_code","").strip()
        asset_name = request.form.get("asset_name","").strip()
        status = request.form.get("status","").strip()

        # Validation
        if not validate_string(asset_code, min_length=1, max_length=100):
            flash("Asset code is required (1-100 chars)", "error")
            return redirect("/assets/create")

        if not validate_string(asset_name, min_length=1, max_length=255):
            flash("Asset name is required (1-255 chars)", "error")
            return redirect("/assets/create")

        if not validate_asset_status(status):
            flash("Invalid asset status selected", "error")
            return redirect("/assets/create")

        conn = get_db_connection()
        
        asset = conn.execute("""
            INSERT INTO assets (
                asset_code,
                asset_name,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            asset_code,
            asset_name,
            status,
            now_wib(),
            now_wib()
        ))
        
        asset_id = asset.lastrowid
        
        create_audit_log(
            session.get("user_id"),
            "CREATE",
            "asset",
            asset_id,
            f"Create new asset: {asset_name}")
        
        conn.commit()

        flash("Asset successfully added", "success")
    except sqlite3.IntegrityError as e:
        logger.error(f"ERROR STORE ASSET: {e}")
        if "asset_code" in str(e).lower():
            flash("Asset code already exists", "error")
        else:
            flash("Data constraint violation", "error")
    except Exception as e:
        resp = handle_db_error(e, user_id=session.get("user_id"), entity_type="asset")
        flash(resp.get('error'), 'error')

    finally:
        if conn:
            conn.close()

    return redirect("/assets")


# ==========================================
# EDIT PAGE
# ==========================================
def asset_edit(id):

    conn = None

    try:
        conn = get_db_connection()

        asset = conn.execute("""
            SELECT *
            FROM assets
            WHERE id = ?
        """, (id,)).fetchone()

        if not asset:
            flash("Asset not found", "error")
            return redirect("/assets")

        return render_template("assets/edit.html", asset=asset)

    except Exception as e:
        logger.error(f"ERROR EDIT ASSET: {e}")
        logger.error(traceback.format_exc())
        flash("Failed to open asset data", "error")
        return redirect("/assets")

    finally:
        if conn:
            conn.close()

# ==========================================
# UPDATE
# ==========================================
def asset_update(id):

    conn = None

    try:
        asset_code = request.form.get("asset_code","").strip()
        asset_name = request.form.get("asset_name","").strip()
        status = request.form.get("status","").strip()

        # Validation
        if not validate_string(asset_code, min_length=1, max_length=100):
            flash("Asset code is required (1-100 chars)", "error")
            return redirect(f"/assets/{id}/edit")

        if not validate_string(asset_name, min_length=1, max_length=255):
            flash("Asset name is required (1-255 chars)", "error")
            return redirect(f"/assets/{id}/edit")

        if not validate_asset_status(status):
            flash("Invalid asset status selected", "error")
            return redirect(f"/assets/{id}/edit")

        conn = get_db_connection()
        old_data = conn.execute("""
            SELECT asset_code, asset_name, status
            FROM assets
            WHERE id = ?
        """, (id,)).fetchone()
        
        changes = []
        
        if old_data["asset_code"] != asset_code:
            changes.append(
                f"asset_code: '{old_data['asset_code']}' -> '{asset_code}'"
            )

        if old_data["asset_name"] != asset_name:
            changes.append(
                f"asset_name: '{old_data['asset_name']}' -> '{asset_name}'"
            )

        if old_data["status"] != status:
            changes.append(
                f"status: '{old_data['status']}' -> '{status}'"
            )
            
        detail = ", ".join(changes)
        
        conn.execute("""
            UPDATE assets
            SET
                asset_code = ?,
                asset_name = ?,
                status = ?,
                updated_at = ?
            WHERE id = ?
        """, (asset_code, asset_name, status, now_wib(), id))
        
        create_audit_log(
            session.get("user_id"),
            "UPDATE",
            "asset",
            id,
            f"Update asset: {detail}")

        conn.commit()

        flash("Asset successfully updated", "success")

    except sqlite3.IntegrityError as e:
        logger.error(f"ERROR UPDATE ASSET: {e}")
        if "asset_code" in str(e).lower():
            flash("Asset code already exists", "error")
        else:
            flash("Data constraint violation", "error")
    except Exception as e:
        resp = handle_db_error(e, user_id=session.get("user_id"), entity_type="asset")
        flash(resp.get('error'), 'error')

    finally:
        if conn:
            conn.close()

    return redirect("/assets")


# ==========================================
# SOFT DELETE
# ==========================================

def asset_delete(id):

    conn = None

    try:
        conn = get_db_connection()
        
        old_data = conn.execute("""
            SELECT asset_name
            FROM assets
            WHERE id = ?
        """, (id,)).fetchone()
        
        old_name = old_data["asset_name"]

        conn.execute("""
            UPDATE assets
            SET is_deleted = 1, 
                updated_at = ?
            WHERE id = ?
        """, (now_wib(), id))
        
        create_audit_log(
            session.get("user_id"),
            "DELETE",
            "asset",
            id,
            f"Soft delete asset: {old_name}")

        conn.commit()

        flash("Asset successfully deleted", "warning")
        

    except Exception as e:
        logger.error(f"ERROR SOFT DELETE: {e}")
        logger.error(traceback.format_exc())
        flash("Failed to delete asset", "error")

    finally:
        if conn:
            conn.close()

    return redirect("/assets")


# ==========================================
# RESTORE
# ==========================================
def asset_restore(id):

    conn = None

    try:
        role = session.get("role")

        if role != 0:
            return "Forbidden", 403

        conn = get_db_connection()
        
        old_data = conn.execute("""
            SELECT asset_name
            FROM assets
            WHERE id = ?
        """, (id,)).fetchone()
        
        old_name = old_data["asset_name"]
        
        conn.execute("""
            UPDATE assets
            SET is_deleted = 0, updated_at = ?
            WHERE id = ?
        """, (now_wib(), id))
        
        create_audit_log(
            session.get("user_id"),
            "RESTORE",
            "asset",
            id,
            f"Restore asset: {old_name}")
        
        conn.commit()

        flash("Asset successfully restored", "success")

    except Exception as e:
        logger.error(f"ERROR RESTORE: {e}")
        logger.error(traceback.format_exc())
        flash("Failed to restore asset", "error")

    finally:
        if conn:
            conn.close()

    return redirect("/assets")

# ==========================================
# PERMANENT DELETE
# ==========================================
def asset_delete_permanent(id):

    conn = None

    try:
        role = session.get("role")

        if role != 0:
            return "Forbidden", 403

        conn = get_db_connection()
        
        old_data = conn.execute("""
            SELECT asset_name, asset_code , status
            FROM assets
            WHERE id = ?
        """, (id,)).fetchone()
        
        old_name = old_data["asset_name"]

        conn.execute("""
            DELETE FROM assets
            WHERE id = ?
        """, (id,))
        
        create_audit_log(
            session.get("user_id"),
            "DELETE",
            "asset",
            id,
            f"Permanent delete asset: {old_name}")

        conn.commit()

        flash("Asset permanently deleted", "success")

    except sqlite3.IntegrityError as e:
        logger.error(f"PERMANENT DELETE ASSET IntegrityError: {e}")
        logger.error(traceback.format_exc())
        flash("Cannot permanently delete asset because it is referenced by other records.", "error")

    except Exception as e:
        logger.error(f"ERROR PERMANENT DELETE: {e}")
        logger.error(traceback.format_exc())
        flash("Failed to permanently delete asset", "error")

    finally:
        if conn:
            conn.close()

    return redirect("/assets")