import os
import sys
import sqlite3
import random
from datetime import timedelta

from app.database.connection import get_db_connection
from app.utils.time_helper import now_wib
from werkzeug.security import generate_password_hash

DB_NAME = "instance/auditflow.db"


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
        (0, "Super Admin", "super@greenlogix.com", generate_password_hash("admin123")),
        (1, "Admin", "admin@greenlogix.com", generate_password_hash("admin123")),
        (2, "User", "user@greenlogix.com", generate_password_hash("user123")),
    ]

    cursor.executemany("""
        INSERT INTO users (role, name, email, password)
        VALUES (?, ?, ?, ?)
    """, users)

    # =========================
    # ASSETS
    # =========================
    assets = [
        ("AST-001", "Main Server", "Operational"),
        ("AST-002", "Backup Server", "Maintenance"),
        ("AST-003", "Database Server", "Operational"),
        ("AST-004", "Web Server", "Operational"),
        ("AST-005", "Auth Server", "Broken"),
    ]

    cursor.executemany("""
        INSERT INTO assets (asset_code, asset_name, status)
        VALUES (?, ?, ?)
    """, assets)

    # =========================
    # CATEGORIES
    # =========================
    categories = [
        ("Server Issue", "SEV-1"),
        ("Network Issue", "SEV-2"),
        ("Database Issue", "SEV-1"),
        ("Security Issue", "SEV-1"),
        ("Performance Issue", "SEV-3"),
    ]

    cursor.executemany("""
        INSERT INTO incident_categories (category_name, default_severity)
        VALUES (?, ?)
    """, categories)

    # =========================
    # INCIDENTS (AUTO 1 MONTH DATA)
    # =========================
    statuses = ["Open", "In Progress", "Resolved", "Closed"]
    severities = ["SEV-1", "SEV-2", "SEV-3"]

    incidents = []

    for day in range(1, 31):  # 30 hari
        for _ in range(random.randint(1, 3)):  # 1–3 incident per hari

            incidents.append((
                2,  # user_id (User)
                random.randint(1, len(assets)),
                random.randint(1, len(categories)),
                random.choice(severities),
                random.choice(statuses),
                f"Auto generated incident for day {day}"
            ))

    cursor.executemany("""
        INSERT INTO incidents (
            user_id,
            asset_id,
            incident_category_id,
            severity_level,
            status,
            detail
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, incidents)

    conn.commit()
    conn.close()

    print(f"SEED DONE - {len(incidents)} incidents generated")


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

    else:
        print("Usage: python seed.py [reset|seed|fresh]")