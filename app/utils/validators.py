# ==========================================
# app/utils/validators.py
# Input Validation Helpers
# ==========================================

import re
from datetime import datetime


def validate_email(email):
    """Validate email format"""
    if not email or len(email) > 255:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """Validate password strength (min 6 chars)"""
    if not password or len(password) < 6 or len(password) > 255:
        return False
    return True


def validate_string(value, min_length=1, max_length=255, allow_empty=False):
    """Validate string field"""
    if not value:
        return allow_empty
    if not isinstance(value, str):
        return False
    return min_length <= len(value) <= max_length


def validate_integer(value, min_val=None, max_val=None):
    """Validate integer field"""
    try:
        num = int(value)
        if min_val is not None and num < min_val:
            return False
        if max_val is not None and num > max_val:
            return False
        return True
    except (ValueError, TypeError):
        return False


def validate_date(date_string):
    """Validate date format YYYY-MM-DD"""
    if not date_string:
        return False
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def validate_severity(severity):
    """Validate incident severity"""
    valid_severities = ['SEV-1', 'SEV-2', 'SEV-3', 'SEV-4','SEV-5']
    return severity in valid_severities


def validate_status(status):
    """Validate incident status"""
    valid_statuses = ['Open', 'In Progress', 'Resolved', 'Closed']
    return status in valid_statuses


def validate_asset_status(status):
    """Validate asset status"""
    valid_statuses = ['Operational', 'Maintenance', 'Broken']
    return status in valid_statuses


def validate_role(role):
    """Validate user role"""
    valid_roles = [0, 1, 2]
    try:
        return int(role) in valid_roles
    except (ValueError, TypeError):
        return False
