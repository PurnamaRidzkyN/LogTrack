# ==========================================
# controllers/dashboard_controller.py
# ==========================================

from flask import render_template, session
from datetime import datetime
from app.database.connection import get_db_connection

def dashboard():
    conn = get_db_connection()

    # ==========================================
    # 1. KPI CARDS (Status Terkini)
    # ==========================================

    # SEV-1 ACTIVE (Hanya yang belum Resolved)
    critical_incident = conn.execute(
        """
        SELECT COUNT(*) as total 
        FROM incidents 
        WHERE severity_level = 'SEV-1' AND status != 'Resolved'
        """
    ).fetchone()

    # PENDING TASKS (Hitung status Open dan In Progress sekaligus)
    tasks = conn.execute(
        """
        SELECT 
            SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) as open_count,
            SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as progress_count
        FROM incidents
        """
    ).fetchone()

    # ASSETS (Broken & Total)
    asset_stats = conn.execute(
        """
        SELECT 
            COUNT(*) as total_assets,
            SUM(CASE WHEN status = 'Broken' THEN 1 ELSE 0 END) as broken_total
        FROM assets
        """
    ).fetchone()

    # Konstruksi ulang format dict agar sesuai dengan template HTML
    broken_asset = {'total': asset_stats['broken_total'] or 0}
    total_assets = asset_stats['total_assets'] or 0

    # TODAY REPORT (Gunakan waktu lokal SQLite)
    today_report = conn.execute(
        """
        SELECT COUNT(*) as total 
        FROM incidents 
        WHERE DATE(created_at) = DATE('now', 'localtime')
        """
    ).fetchone()

    current_time = datetime.now().strftime("%d %b %Y, %H:%M")


    # ==========================================
    # 2. ATTENTION QUEUE (SEV-1 yang harus segera ditangani)
    # ==========================================
    
    critical_queue = conn.execute(
        """
        SELECT 
            i.id, i.created_at, 
            a.asset_name, a.asset_code, 
            c.category_name
        FROM incidents i
        LEFT JOIN assets a ON a.id = i.asset_id
        LEFT JOIN incident_categories c ON c.id = i.incident_category_id
        WHERE i.severity_level = 'SEV-1' AND i.status != 'Resolved'
        ORDER BY i.created_at ASC
        LIMIT 5
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
        WHERE status = 'Broken'
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
        WHERE DATE(created_at) >= DATE('now', '-6 days', 'localtime')
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at) ASC
        """
    ).fetchall()

    trend_labels = [row['report_date'] for row in trend_query]
    trend_data = [row['total'] for row in trend_query]

    # B. DONUT CHART (Rasio Kategori Insiden)
    category_query = conn.execute(
        """
        SELECT c.category_name, COUNT(i.id) as total
        FROM incidents i
        LEFT JOIN incident_categories c ON c.id = i.incident_category_id
        GROUP BY c.id
        """
    ).fetchall()

    cat_labels = [row['category_name'] for row in category_query]
    cat_data = [row['total'] for row in category_query]

    conn.close()

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
        cat_data=cat_data
        )