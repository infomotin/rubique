"""
CubePermutation AI - Role-Based Access Control (RBAC) Decorators Module
========================================================================
Route decorators for session authentication, multi-role authorization, and API
protection.

Easy Description:
- @login_required: Ensures a user is signed in before viewing a page; redirects guests to login.
- @role_required: Restricts sensitive admin/developer pages to specific authorized roles.
- @api_login_required: Protects AJAX and JSON API endpoints by returning 401 Unauthorized status.
"""

from functools import wraps
from flask import session, request, redirect, url_for, flash, jsonify


def login_required(view_func):
    """
    Decorator to protect views requiring an authenticated session.
    Redirects unauthenticated visitors to the login page.
    """
    @wraps(view_func)
    def decorated_view(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        return view_func(*args, **kwargs)
    return decorated_view


def role_required(*allowed_roles):
    """
    Decorator to restrict access to users possessing specific roles (e.g. 'super_admin', 'developer').
    """
    def decorator(view_func):
        @wraps(view_func)
        def decorated_view(*args, **kwargs):
            if not session.get('user_id'):
                flash('Please log in to access this area.', 'warning')
                return redirect(url_for('auth.login', next=request.path))
            
            user_role = session.get('role', 'subscriber')
            if user_role not in allowed_roles:
                flash('Access denied: You do not possess the required security privileges.', 'danger')
                return redirect(url_for('home.index'))
                
            return view_func(*args, **kwargs)
        return decorated_view
    return decorator


def api_login_required(view_func):
    """
    Decorator for JSON/AJAX API endpoints requiring authentication.
    Returns HTTP 401 JSON error instead of an HTML redirect.
    """
    @wraps(view_func)
    def decorated_view(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({
                "status": "error",
                "success": False,
                "message": "Authentication required. Please log in."
            }), 401
        return view_func(*args, **kwargs)
    return decorated_view


def api_role_required(*allowed_roles):
    """
    Decorator for JSON/AJAX API endpoints requiring specific roles.
    Returns HTTP 403 JSON error if user lacks privilege.
    """
    def decorator(view_func):
        @wraps(view_func)
        def decorated_view(*args, **kwargs):
            if not session.get('user_id'):
                return jsonify({
                    "status": "error",
                    "success": False,
                    "message": "Authentication required."
                }), 401
            
            user_role = session.get('role', 'subscriber')
            if user_role not in allowed_roles:
                return jsonify({
                    "status": "error",
                    "success": False,
                    "message": "Forbidden: Insufficient privileges."
                }), 403
                
            return view_func(*args, **kwargs)
        return decorated_view
    return decorator
