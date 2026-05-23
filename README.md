# LogTrack (Greenfield)

LogTrack is a Flask-based incident management and audit trail application built as an MVP for manufacturing and operational incident tracking. It implements a 5-tier Severity Matrix (based on IPQI/ITSM standards) to prioritize catastrophic failures over minor glitches.

It supports incident tracking, asset management, incident categories, user roles, audit logging, and dashboard prioritization for urgent issues.

## Key Features

- Incident CRUD with severity classification and status tracking
- Asset CRUD with status information and soft-delete support
- Incident category CRUD with default severity mapping
- User CRUD with role-based rules and soft-delete handling
- Audit log tracking for create/update/delete actions
- Search, date filtering, and export CSV for incidents
- Dashboard KPIs and emergency highlighting for urgent incidents
- Timezone-aware timestamps using Asia/Jakarta (WIB)

## MVP Fit

This project is designed around `Opsi C: Audit & Incident Logs` and includes:

- Functional data management for all entities
- Audit trail for user activity and changes
- Attention logic for incident urgency and severity
- Raw SQL-based database layer with no ORM
- Soft-delete behavior on key entities

## Requirements

- Python 3.8 or newer
- `pip` package manager
- SQLite (bundled with Python)

## Setup

### 1. Create a virtual environment

Windows:

```powershell
python -m venv venv
venv\Scripts\activate
```

Linux / macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and update values if needed:

```bash
copy .env.example .env
```

Example variables:

```ini
SECRET_KEY=your_secret_key_here
DATABASE_PATH=instance/logtrack.db
DEBUG=true
```

### 4. Seed the database

```bash
python seed.py fresh

```

This command:

* creates the SQLite schema
* inserts sample users, 15 manufacturing assets, and 15 incident categories
* generates **90 days (3 months)** of incident data (**2–6 incidents per day**) with weighted SEV-1 to SEV-5 distribution.

```

## Run the application

```bash
python run.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Project structure

- `app/` — source code
  - `controllers/` — request handlers and business logic
  - `routes/` — URL route registration
  - `templates/` — Jinja2 views
  - `utils/` — helpers, validators, and error handling
  - `database/` — schema and seed scripts
- `instance/` — runtime SQLite database file
- `requirements.txt` — Python dependencies
- `run.py` — application entrypoint

## Deployment notes

This application is suitable for an internal VM staging environment with limited resources.

Recommended target platform:

- Ubuntu 22.04 LTS
- 1 CPU core, 2 GB RAM

For production readiness, use a phased rollout model:

1. deploy to staging
2. validate functionality
3. migrate to production

## Notes for production

- The current design uses raw SQL and SQLite for simplicity.
- For higher availability and scalability, consider moving to a dedicated SQL database server.
- Keep `DEBUG=false` in production.


