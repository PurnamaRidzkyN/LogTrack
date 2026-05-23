# ==========================================
# app/utils/error_handler.py
# Error Handling Utilities
# ==========================================

from flask import render_template, jsonify, redirect, url_for, flash
from app.controllers.audit_logs import create_audit_log
import traceback
import logging

logger = logging.getLogger(__name__)


def handle_db_error(error, user_id=None, entity_type="Unknown"):
    """Handle database operation errors with logging"""
    error_msg = f"Database error in {entity_type}: {str(error)}"
    logger.error(error_msg)
    logger.error(traceback.format_exc())
    
    if user_id:
        try:
            create_audit_log(
                user_id=user_id,
                action_type="Error",
                entity_type=entity_type,
                entity_id=0,
                detail=f"Database error: {str(error)[:100]}"
            )
        except:
            pass
    
    return {
        'error': 'A database error occurred. Please try again.',
        'status': 500
    }


def handle_validation_error(errors):
    """Format validation errors"""
    if isinstance(errors, list):
        return ', '.join(errors)
    return str(errors)


def handle_unauthorized():
    """Handle unauthorized access"""
    flash("You do not have permission to perform this action", "error")
    return redirect(url_for("dashboard"))


def handle_not_found(entity_name):
    """Handle resource not found"""
    flash(f"{entity_name} not found", "error")
    return None


def handle_conflict_error(message):
    """Handle conflict errors (duplicate entries, etc)"""
    return {
        'error': message,
        'status': 409
    }
