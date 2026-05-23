# Deployment Guide

This guide explains how to deploy the LogTrack application to an Ubuntu 22.04 VM in a staged workflow.

## Target Environment

- OS: Ubuntu 22.04 LTS
- CPU: 1 core
- RAM: 2 GB
- Database: SQLite (local file)
- App server: Python + Flask

## Deployment Strategy

1. **Staging environment**
   - Deploy first to a staging VM.
   - Validate application flow, login, CRUD operations, incident dashboard, and export.
   - Confirm audit logs and soft-delete behavior.

2. **Production rollout**
   - Once staging is verified, deploy to production VM.
   - Use a phased deployment with a short validation window.
   - Keep a backup of the SQLite database file before switching traffic.

## Prerequisites

Install packages:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
```

## Clone repository

```bash
cd /opt
sudo git clone <your-repo-url> logtrack
cd logtrack
```

## Create Python virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Configure environment variables

Copy the example file and set production values:

```bash
cp .env.example .env
```

Edit `.env` and set:

```ini
SECRET_KEY=supersecretkey
DATABASE_PATH=instance/logtrack.db
DEBUG=false
```

## Initialize the database

```bash
python -m app.database.seed fresh
```

This command creates the database schema and seeds sample data.

## Run the application manually

```bash
python run.py
```

Access the app at:

```text
http://127.0.0.1:5000
```

## Recommended process management

For a production-like setup, use `gunicorn` and a systemd service.

### Install Gunicorn

```bash
pip install gunicorn
```

### Example systemd service

Create `/etc/systemd/system/logtrack.service` with:

```ini
[Unit]
Description=LogTrack Flask Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/logtrack
EnvironmentFile=/opt/logtrack/.env
ExecStart=/opt/logtrack/venv/bin/gunicorn --workers 2 --bind 0.0.0.0:5000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Reload and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable logtrack
sudo systemctl start logtrack
sudo systemctl status logtrack
```

## Reverse proxy (optional)

For external access, use Nginx as a reverse proxy to forward traffic to Gunicorn.

### Install Nginx

```bash
sudo apt install -y nginx
```

### Example Nginx config

Create `/etc/nginx/sites-available/logtrack`:

```nginx
server {
    listen 80;
    server_name your.domain.or.ip;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and reload Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/logtrack /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Backup and rollback

- Back up the SQLite database file before deploy or migration:

```bash
cp instance/logtrack.db instance/logtrack.db.bak
```

- Rollback by restoring the backup file:

```bash
cp instance/logtrack.db.bak instance/logtrack.db
```

## Validation checklist

- [ ] Application starts successfully
- [ ] Login works
- [ ] Incident create/update/delete works
- [ ] Asset CRUD works
- [ ] Category CRUD works
- [ ] Audit logs record actions
- [ ] Dashboard loads and shows KPI counts
- [ ] Export CSV works

## Notes

- For production, set `DEBUG=false`.
- SQLite is fine for small internal deployments, but consider a proper SQL server for higher scale.
- Keep the VM OS updated and monitor resource usage on 1 core / 2 GB RAM.
