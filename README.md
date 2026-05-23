# AuditFlow (Greenfield)

A simple web application for tracking incidents, assets, categories, and audit trails.

**Main features**

- User, asset, incident category, and incident management
- Audit logs for CRUD actions
- Seeder to populate example data (including 30 days of incidents)

**Requirements**

- Python 3.8+
- Packages listed in `requirements.txt`

## Setup (Windows)

1. Create and activate a virtual environment:

```
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies:

```
pip install -r requirements.txt
```

3. (Optional) Create a `.env` file in the project root if you want custom configuration:

```
SECRET_KEY=your_secret_key_here
DATABASE_PATH=instance/auditflow.db
DEBUG=true
```

4. Reset and seed the database (this removes the old DB):

```
python -m app.database.seed fresh
```

The seeder will:

- Create the schema in `instance/auditflow.db` if it does not exist
- Insert users, assets, and incident categories
- Generate incident records for the last 30 days (1–3 incidents per day) in the Asia/Jakarta timezone

## Running the application

```
python run.py
```

Or use Flask run:

```
set FLASK_APP=run.py
flask run
```

The default server will run at `http://127.0.0.1:5000`.

## Important structure

- `app/` : application source code (controllers, templates, utils)
- `app/database/schema.sql` : SQLite schema definition
- `app/database/seed.py` : script to seed initial data
- `instance/auditflow.db` : SQLite database file created by the seeder

## Notes

- The `created_at` and `updated_at` timestamps use Asia/Jakarta timezone via `app/utils/time_helper.py`.
- To change seeder behavior (for example, incidents per day), update `app/database/seed.py`.

If you want, I can also pin package versions in `requirements.txt` or add a `.env.example` file.
