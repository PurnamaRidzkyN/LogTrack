# ==========================================
# controllers/dashboard_controller.py
# ==========================================

from flask import render_template, session, flash, redirect, url_for
from datetime import datetime
from app.database.connection import get_db_connection
import logging
import traceback

logger = logging.getLogger(__name__)

def dashboard():
    conn = None
    try:
        conn = get_db_connection()

        # ==========================================
        # 1. KPI CARDS (Status Terkini) - COMBINED QUERIES
        # ==========================================

        # Combined incident metrics (4 KPIs in 1 query)
        incident_metrics = conn.execute(
            """
            SELECT 
                SUM(
                    CASE 
                        WHEN severity_level = 'SEV-1'
                        AND status NOT IN ('Resolved', 'Closed')
                        THEN 1 
                        ELSE 0 
                    END
                ) as critical_total,

                SUM(
                    CASE 
                        WHEN status = 'Open'
                        THEN 1 
                        ELSE 0 
                    END
                ) as open_count,

                SUM(
                    CASE 
                        WHEN status = 'In Progress'
                        THEN 1 
                        ELSE 0 
                    END
                ) as progress_count,

                SUM(
                    CASE 
                        WHEN DATE(created_at) =
                        DATE('now', 'localtime')
                        THEN 1 
                        ELSE 0 
                    END
                ) as today_total

            FROM incidents
            WHERE is_deleted = 0
            """
        ).fetchone()

        critical_incident = {'total': incident_metrics['critical_total'] or 0}
        tasks = {'open_count': incident_metrics['open_count'] or 0, 'progress_count': incident_metrics['progress_count'] or 0}
        today_report = {'total': incident_metrics['today_total'] or 0}

        # Asset metrics
        asset_stats = conn.execute(
            """
            SELECT 
                COUNT(*) as total_assets,
                SUM(CASE WHEN status = 'Broken' THEN 1 ELSE 0 END) as broken_total
            FROM assets
            where is_deleted = 0
            """
        ).fetchone()

        broken_asset = {'total': asset_stats['broken_total'] or 0}
        total_assets = asset_stats['total_assets'] or 0

        current_time = datetime.now().strftime("%d %b %Y, %H:%M")


        # ==========================================
        # 2. ATTENTION QUEUE (SEV-1 yang harus segera ditangani)
        # ==========================================
        
        critical_queue = conn.execute(
            """
            SELECT 
                i.id, i.created_at, 
                a.asset_name, a.asset_code, 
                c.category_name, i.severity_level
            FROM incidents i
            LEFT JOIN assets a ON a.id = i.asset_id
            LEFT JOIN incident_categories c ON c.id = i.incident_category_id
            WHERE i.severity_level IN ('SEV-1', 'SEV-2') AND i.status NOT IN ('Resolved', 'Closed')
            and i.is_deleted = 0
            ORDER BY i.severity_level ASC, i.created_at ASC
            LIMIT 7
            """
        ).fetchall()


        # ==========================================
        # 3. STAGNANT BROKEN ASSETS (Aset mangkrak)
        # ==========================================
        
        # SQLite menghitung selisih hari menggunakan julianday()
        stagnant_broken = conn.execute(
            """
            SELECT 
                asset_code, asset_name,
                CAST(julianday('now', 'localtime') - julianday(updated_at) AS INTEGER) as downtime_days
            FROM assets
            WHERE status = 'Broken' and is_deleted = 0
            ORDER BY updated_at ASC
            LIMIT 5
            """
        ).fetchall()


        # ==========================================
        # 4. CHART DATA FORMATTING (Tren Mingguan & Kategori)
        # ==========================================

        # A. TREND MINGGUAN (7 Hari Terakhir)
        trend_query = conn.execute(
            """
            SELECT DATE(created_at) as report_date, COUNT(id) as total
            FROM incidents
            WHERE DATE(created_at) >= DATE('now', '-6 days', 'localtime') and is_deleted = 0
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at) ASC
            """
        ).fetchall()

        trend_labels = [row['report_date'] for row in trend_query]
        trend_data = [row['total'] for row in trend_query]

        # B. DONUT CHART (Rasio Kategori Insiden)
        category_query = conn.execute("""
        SELECT c.category_name, COUNT(i.id) as total
        FROM incidents i
        LEFT JOIN incident_categories c ON c.id = i.incident_category_id
        where i.is_deleted = 0
        GROUP BY c.id
        ORDER BY total DESC
        """).fetchall()

        cat_labels = []
        cat_data = []

        others_total = 0

        for idx, row in enumerate(category_query):
            name = row["category_name"] or "Unknown"
            total = row["total"]

            if idx < 5:
                cat_labels.append(name)
                cat_data.append(total)
            else:
                others_total += total

        if others_total > 0:
            cat_labels.append("Others")
            cat_data.append(others_total)
        
        rows = conn.execute("""
        SELECT 
            a.asset_name,
            COUNT(i.id) AS total_incidents
        FROM incidents i
        JOIN assets a ON i.asset_id = a.id
        WHERE i.is_deleted = 0
        GROUP BY a.id
        ORDER BY total_incidents DESC
        LIMIT 5
        """).fetchall()

        asset_labels = [row["asset_name"] for row in rows]
        asset_data = [row["total_incidents"] for row in rows]

        # Lempar semua variabel ke template
        return render_template(
            "dashboard/index.html",
            role=session.get("role"),
            current_time=current_time,
            
            # KPI Cards
            critical_incident=critical_incident,
            open_count=tasks['open_count'] or 0,
            progress_count=tasks['progress_count'] or 0,
            broken_asset=broken_asset,
            total_assets=total_assets,
            today_report=today_report,
            
            # Tables
            critical_queue=critical_queue,
            stagnant_broken=stagnant_broken,
            
            # Charts (Otomatis diubah jadi list python yang dimengerti Chart.js)
            trend_labels=trend_labels,
            trend_data=trend_data,
            cat_labels=cat_labels,
            cat_data=cat_data,
            
            asset_labels=asset_labels,
            asset_data=asset_data
        )

    except Exception as e:
        logger.error(f"DASHBOARD ERROR: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        flash("An error occurred while loading dashboard data", "error")
        return render_template(
            "dashboard/index.html",
            role=session.get("role"),
            current_time=datetime.now().strftime("%d %b %Y, %H:%M"),
            critical_incident={'total': 0},
            open_count=0,
            progress_count=0,
            broken_asset={'total': 0},
            total_assets=0,
            today_report={'total': 0},
            critical_queue=[],
            stagnant_broken=[],
            trend_labels=[],
            trend_data=[],
            cat_labels=[],
            cat_data=[],
            asset_labels=[],
            asset_data=[]
        )

    finally:
        if conn:
            conn.close()