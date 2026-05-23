-- ==========================================
-- USERS
-- ==========================================

CREATE TABLE users (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    role INTEGER NOT NULL,

    name VARCHAR(255) NOT NULL,

    email VARCHAR(255) UNIQUE NOT NULL,

    password VARCHAR(255) NOT NULL,

    created_at DATETIME,

    is_deleted INTEGER DEFAULT 0
);


-- ==========================================
-- ASSETS
-- ==========================================

CREATE TABLE assets (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    asset_code VARCHAR(255) UNIQUE NOT NULL,

    asset_name VARCHAR(255) NOT NULL,

    status VARCHAR(50) DEFAULT 'Operational',

    created_at DATETIME,

    updated_at DATETIME,

    is_deleted INTEGER DEFAULT 0
);


-- =======================================a===
-- INCIDENT CATEGORIES
-- ==========================================

CREATE TABLE incident_categories (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    category_name VARCHAR(255) NOT NULL,

    default_severity VARCHAR(50) NOT NULL,

    created_at DATETIME,

    updated_at DATETIME,

    is_deleted INTEGER DEFAULT 0
);


-- ==========================================
-- AUDIT INCIDENT LOGS
-- ==========================================

CREATE TABLE incidents (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER,

    asset_id INTEGER,

    incident_category_id INTEGER,
    
    handled_by INTEGER,

    severity_level VARCHAR(50) NOT NULL,

    status VARCHAR(255) NOT NULL,

    detail TEXT,

    created_at DATETIME,

    updated_at DATETIME,

    is_deleted INTEGER DEFAULT 0,

    FOREIGN KEY (user_id)
        REFERENCES users(id),

    FOREIGN KEY (asset_id)
        REFERENCES assets(id),

    FOREIGN KEY (incident_category_id)
        REFERENCES incident_categories(id)
    
    FOREIGN KEY (handled_by)
        REFERENCES users(id)
);

CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action_type VARCHAR(50),
    entity_type VARCHAR(50),
    entity_id INTEGER,
    detail TEXT,
    created_at DATETIME
);