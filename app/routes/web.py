# ==========================================
# routes/web.py
# ==========================================
from app.middlewares.auth import login_required , admin_required , superadmin_required

# AUTH CONTROLLER
from app.controllers.auth_controller import (
    login,
    login_post,
    change_password_update,
    change_password,
    logout
)

# DASHBOARD CONTROLLER
from app.controllers.dashboard_controller import dashboard

# INCIDENT CONTROLLER
from app.controllers.incident_controller import (
    incident_index,
    incident_detail,
    incident_create,
    incident_store,
    incident_edit,
    incident_update,
    incident_delete,
    incident_restore,
    incident_delete_permanent,
    api_assets,
    api_categories,
    export_incidents_csv
)

# ASSET CONTROLLER
from app.controllers.asset_controller import (
    asset_index,
    asset_create,
    asset_store,
    asset_edit,
    asset_update,
    asset_delete,
    asset_restore,
    asset_delete_permanent    
)
# INCIDENT CATEGORY CONTROLLER
from app.controllers.incident_category_controller import (
    incident_category_index,
    incident_category_create,
    incident_category_store,
    incident_category_edit,
    incident_category_update,
    incident_category_delete,
    incident_category_delete_permanent,
    incident_category_restore
)

from app.controllers.audit_logs import (
    audit_log_index
)
from app.controllers.user_controller import (
    user_index,
    user_create,
    user_store,
    user_delete,
    user_restore,
    user_force_delete,
    user_reset_password
)

# ==========================================
# REGISTER ROUTES
# ==========================================

def register_routes(app):

    # ==========================================
    # AUTH
    # ==========================================

    app.add_url_rule(
        "/",
        view_func=login,
        methods=["GET"],
        endpoint="login"
    )

    app.add_url_rule(
        "/login",
        view_func=login,
        methods=["GET"],
        endpoint="login_page"
    )

    app.add_url_rule(
        "/login",
        view_func=login_post,
        methods=["POST"],
        endpoint="login_post"
    )
    
    app.add_url_rule(
        "/change-password",
        view_func=login_required(change_password),
        methods=["GET"],
        endpoint="change_password"
    )
    
    app.add_url_rule(
        "/change-password-post",
        view_func=login_required(change_password_update),
        methods=["POST"],
        endpoint="change_password_post"
    )

    app.add_url_rule(
        "/logout",
        view_func=logout,
        endpoint="logout"
    )


    # ==========================================
    # DASHBOARD
    # ==========================================

    app.add_url_rule(
        "/dashboard",
        view_func=login_required(admin_required(dashboard)),
        endpoint="dashboard"
    )


    # ==========================================
    # INCIDENTS
    # ==========================================

    app.add_url_rule(
        "/incidents",
        view_func=login_required(incident_index),
        endpoint="incident_index"
    )
    
    app.add_url_rule(
        "/incidents/<int:id>",
        view_func=login_required(incident_detail),
        endpoint="incident_detail"
    )
    
    app.add_url_rule(
        "/incidents/create",
        view_func=login_required(incident_create),
        endpoint="incident_create"
    )
    
    app.add_url_rule(
        "/incidents/store",
        view_func=login_required(incident_store),
        methods=["POST"],
        endpoint="incident_store"
    )
    
    app.add_url_rule(
        "/incidents/<int:id>/edit",
        view_func=login_required(admin_required(incident_edit)),
        endpoint="incident_edit"
    )
    
    app.add_url_rule(
        "/incidents/<int:id>/update",
        view_func=login_required(admin_required(incident_update)),
        methods=["POST"],
        endpoint="incident_update"
    )
    
    app.add_url_rule(
        "/incidents/<int:id>/delete",
        view_func=login_required((incident_delete)),
        methods=["POST"],
        endpoint="incident_delete"
    )
    
    app.add_url_rule(
        "/incidents/<int:id>/restore",
        view_func=login_required(superadmin_required(incident_restore)),
        methods=["POST"],
        endpoint="incident_restore"
    )
    
    app.add_url_rule(
        "/incidents/<int:id>/delete-permanent",
        view_func=login_required(superadmin_required(incident_delete_permanent)),
        methods=["POST"],
        endpoint="incident_delete_permanent"
    )
    
    app.add_url_rule(
        "/api/assets",
        view_func=login_required(api_assets),
        endpoint="api_assets"
    )
    app.add_url_rule(
        "/api/categories",
        view_func=login_required(api_categories),
        endpoint="api_categories"
    )
    app.add_url_rule(
        "/export-incidents-csv",
        view_func=login_required(admin_required(export_incidents_csv)),
        endpoint="export_incidents_csv"
    )
    # ==========================================
    # ASSETS
    # ==========================================

    app.add_url_rule(
        "/assets",
        view_func=login_required(admin_required(asset_index)),
        endpoint="asset_index"
    )

    app.add_url_rule(
        "/assets/create",
        view_func=login_required(admin_required(asset_create)),
        endpoint="asset_create"
    )

    app.add_url_rule(
        "/assets/store",
        view_func=login_required(admin_required(asset_store)),
        methods=["POST"],
        endpoint="asset_store"
    )

    app.add_url_rule(
        "/assets/<int:id>/edit",
        view_func=login_required(admin_required(asset_edit)),
        endpoint="asset_edit"
    )

    app.add_url_rule(
        "/assets/<int:id>/update",
        view_func=login_required(admin_required(asset_update)),
        methods=["POST"],
        endpoint="asset_update"
    )

    app.add_url_rule(
        "/assets/<int:id>/delete",
        view_func=login_required(admin_required(asset_delete)),
        methods=["POST"],
        endpoint="asset_delete"
    )
    
    app.add_url_rule(
        "/assets/<int:id>/delete-permanent",
        view_func=login_required(superadmin_required(asset_delete_permanent)),
        methods=["POST"],
        endpoint="asset_delete_permanent"
    )
    
    app.add_url_rule(
        "/assets/<int:id>/restore",
        view_func=login_required(superadmin_required(asset_restore)),
        methods=["POST"],
        endpoint="asset_restore"
    )
    
    # ==========================================
    # INCIDENT CATEGORIES
    # ==========================================

    app.add_url_rule(
        "/incident_categories",
        view_func=login_required(admin_required(incident_category_index)),
        endpoint="incident_category_index"
    )

    app.add_url_rule(
        "/incident_categories/create",
        view_func=login_required(admin_required(incident_category_create)),
        endpoint="incident_category_create"
    )

    app.add_url_rule(
        "/incident_categories/store",
        view_func=login_required(admin_required(incident_category_store)),
        methods=["POST"],
        endpoint="incident_category_store"
    )

    app.add_url_rule(
        "/incident_categories/<int:id>/edit",
        view_func=login_required(admin_required(incident_category_edit)),
        endpoint="incident_category_edit"
    )

    app.add_url_rule(
        "/incident_categories/<int:id>/update",
        view_func=login_required(admin_required(incident_category_update)),
        methods=["POST"],
        endpoint="incident_category_update"
    )

    app.add_url_rule(
        "/incident_categories/<int:id>/delete",
        view_func=login_required(admin_required(incident_category_delete)),
        methods=["POST"],
        endpoint="incident_category_delete"
    )
    
    app.add_url_rule(
        "/incident_categories/<int:id>/delete-permanent",
        view_func=login_required(superadmin_required(incident_category_delete_permanent)),
        methods=["POST"],
        endpoint="incident_category_delete_permanent"
    )
    
    app.add_url_rule(
        "/incident_categories/<int:id>/restore",
        view_func=login_required(superadmin_required(incident_category_restore)),
        methods=["POST"],
        endpoint="incident_category_restore"
    )
    
    
    # ==========================================
    # AUDIT LOGS
    # ==========================================
    app.add_url_rule(
        "/audit_logs",
        view_func=login_required(superadmin_required(audit_log_index)),
        endpoint="audit_log_index"
    )
    
    # ==========================================
    # USERS
    # ==========================================
    app.add_url_rule(
        "/users",
        view_func=login_required(admin_required(user_index)),
        endpoint="user_index"
    )
    
    app.add_url_rule(
        "/users/create",
        view_func=login_required(admin_required(user_create)),
        endpoint="user_create"
    )
    
    app.add_url_rule(
        "/users/store", 
        view_func=login_required(admin_required(user_store)),
        methods=["POST"],
        endpoint="user_store"
    )
    
    app.add_url_rule(
        "/users/<int:id>/delete",
        view_func=login_required(admin_required(user_delete)),
        methods=["POST"],
        endpoint="user_delete"
    )
    
    app.add_url_rule(
        "/users/<int:id>/restore",
        view_func=login_required(superadmin_required(user_restore)),
        methods=["POST"],
        endpoint="user_restore"
    )
    
    app.add_url_rule(
        "/users/<int:id>/delete-permanent",
        view_func=login_required(superadmin_required(user_force_delete)),
        methods=["POST"],
        endpoint="user_force_delete"
    )
    
    app.add_url_rule(
        "/users/<int:id>/reset-password",
        view_func=login_required(admin_required(user_reset_password)),
        methods=["POST"],
        endpoint="user_reset_password"
    )