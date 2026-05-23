import os
import sys
import sqlite3
import random
import pytz
from datetime import datetime, timedelta

from app.database.connection import get_db_connection
from app.utils.time_helper import now_wib
from werkzeug.security import generate_password_hash

from dotenv import load_dotenv
load_dotenv()

DB_NAME = os.getenv("DATABASE_PATH")


def seed_superadmin():
    conn = get_db_connection()
    cursor = conn.cursor()

    # =========================
    # USERS
    # =========================
    users = [
        (0, "Super Admin", "purnamanugraha492@gmail.com", generate_password_hash("admin123"))
    ]
    cursor.executemany("""
        INSERT INTO users (role, name, email, password)
        VALUES (?, ?, ?, ?)
    """, users)


# ==========================================
# CREATE SCHEMA
# ==========================================
def create_schema():
    conn = sqlite3.connect(DB_NAME)

    with open("app/database/schema.sql", "r") as f:
        conn.executescript(f.read())

    conn.commit()
    conn.close()

    print("SCHEMA CREATED")


# ==========================================
# RESET DATABASE (FULL CLEAN)
# ==========================================
def reset_db():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print("OLD DB DELETED")

    create_schema()
    print("DB RESET DONE")


# ==========================================
# SEED DATA
# ==========================================
def seed():
    conn = get_db_connection()
    cursor = conn.cursor()

    # =========================
    # USERS
    # =========================
    users = [
        (0, "Super Admin", "purnamanugraha492@gmail.com", generate_password_hash("admin123")),
        (1, "Admin", "ops@gmail.com", generate_password_hash("admin123")),
        (2, "user", "user@gmail.com", generate_password_hash("user123")),
    ]

    cursor.executemany("""
        INSERT INTO users (role, name, email, password)
        VALUES (?, ?, ?, ?)
    """, users)

    # =========================
    # ASSETS (15 MANUFACTURING ASSETS)
    # =========================
    assets = [
        ("AST-001", "Production Line A", "Operational", now_wib(), now_wib()),
        ("AST-002", "Production Line B", "Operational", now_wib(), now_wib()),
        ("AST-003", "CNC Milling Machine 01", "Operational", now_wib(), now_wib()),
        ("AST-004", "CNC Lathe Machine 02", "Maintenance", now_wib(), now_wib()),
        ("AST-005", "Assembly Robot Arm Alpha", "Operational", now_wib(), now_wib()),
        ("AST-006", "Automated Packaging Unit", "Operational", now_wib(), now_wib()),
        ("AST-007", "Main Conveyor Belt", "Operational", now_wib(), now_wib()),
        ("AST-008", "Quality Inspection Scanner", "Operational", now_wib(), now_wib()),
        ("AST-009", "Industrial Boiler System", "Broken", now_wib(), now_wib()),
        ("AST-010", "Cooling Tower Central", "Broken", now_wib(), now_wib()),
        ("AST-011", "Heavy Duty Air Compressor", "Broken", now_wib(), now_wib()),
        ("AST-012", "Warehouse Forklift Fleet", "Broken", now_wib(), now_wib()),
        ("AST-013", "Backup Generator Set", "Broken", now_wib(), now_wib()),
        ("AST-014", "HVAC Factory System", "Operational", now_wib(), now_wib()),
        ("AST-015", "Local Server Rack", "Operational", now_wib(), now_wib()),
    ]

    cursor.executemany("""
        INSERT INTO assets (asset_code, asset_name, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """, assets)

    # =========================
    # CATEGORIES (15 MANUFACTURING ISSUES MAPPED TO SEV 1-5)
    # =========================
    categories = [
        # SEV-1: Catastrophic
        ("Catastrophic Machine Failure", "SEV-1", now_wib()),
        ("Total Power Outage", "SEV-1", now_wib()),
        ("Critical Safety Hazard", "SEV-1", now_wib()),
        
        # SEV-2: Major
        ("Core System Overheating", "SEV-2", now_wib()),
        ("Partial Network Downtime", "SEV-2", now_wib()),
        ("Heavy Mechanical Breakdown", "SEV-2", now_wib()),
        
        # SEV-3: Moderate
        ("Fluid / Chemical Leakage", "SEV-3", now_wib()),
        ("Sensor Calibration Error", "SEV-3", now_wib()),
        ("Component Wear and Tear", "SEV-3", now_wib()),
        
        # SEV-4: Minor
        ("Minor Production Jam", "SEV-4", now_wib()),
        ("Unusual Machine Vibration", "SEV-4", now_wib()),
        ("Routine Maintenance Request", "SEV-4", now_wib()),
        
        # SEV-5: Negligible
        ("Cosmetic Damage / Scratches", "SEV-5", now_wib()),
        ("Indicator Light Broken", "SEV-5", now_wib()),
        ("Workspace Cleanup Required", "SEV-5", now_wib()),
    ]

    cursor.executemany("""
        INSERT INTO incident_categories (category_name, default_severity, created_at)
        VALUES (?, ?, ?)
    """, categories)

    # =========================
    # INCIDENTS (3 MONTH DATA)
    # =========================
    wib = pytz.timezone("Asia/Jakarta")
    base_date = datetime.now(wib)

    statuses = ["Open", "In Progress", "Resolved", "Closed"]
    severities = ["SEV-1", "SEV-2", "SEV-3", "SEV-4", "SEV-5"]

    incidents = []

    for day_offset in range(90):  # 3 BULAN = 90 HARI
        day_date = base_date - timedelta(days=day_offset)

        # lebih realistis: 2–6 incident per hari
        for _ in range(random.randint(2, 6)):

            created_at = day_date.replace(
                hour=random.randint(0, 23),
                minute=random.randint(0, 59),
                second=random.randint(0, 59),
                microsecond=0
            )

            # Bobot probabilitas: SEV-4 dan SEV-5 lebih sering terjadi daripada SEV-1
            chosen_severity = random.choices(
                population=severities,
                weights=[0.1, 0.15, 0.25, 0.3, 0.2], 
                k=1
            )[0]

            incidents.append((
                2,  # user_id (Operator)
                random.randint(1, len(assets)),
                random.randint(1, len(categories)),
                chosen_severity,
                random.choice(statuses),
                f"Manufacturing incident auto-generated D-{day_offset}. Checked by operator.",
                created_at.strftime("%Y-%m-%d %H:%M:%S")
            ))

    cursor.executemany("""
        INSERT INTO incidents (
            user_id,
            asset_id,
            incident_category_id,
            severity_level,
            status,
            detail,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, incidents)

    conn.commit()
    conn.close()

    print(f"SEED DONE - {len(incidents)} manufacturing incidents (3 months) with SEV 1-5")

# ==========================================
# CLI RUNNER
# ==========================================
if __name__ == "__main__":

    if len(sys.argv) > 1:

        if sys.argv[1] == "reset":
            reset_db()

        elif sys.argv[1] == "seed":
            seed()

        elif sys.argv[1] == "fresh":
            reset_db()
            seed()
        elif sys.argv[1] == "superadmin":
            seed_superadmin()
            
    else:
        print("Usage: python seed.py [reset|seed|fresh|superadmin]")