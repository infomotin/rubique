"""
CubePermutation AI - Home & Landing Controller (MVC Pattern)
============================================================
Handles high-graphical landing page with interactive math diagrams,
feature overviews, and group theory introduction.
"""

from flask import Blueprint, render_template, session, redirect, url_for

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def index():
    """
    High-Graphic Landing Page:
    If user is authenticated, redirect directly to their default News Feed / Dashboard.
    Otherwise show landing page.
    """
    if session.get('user_id'):
        role = session.get('role', 'user')
        if role == 'super_admin':
            return redirect(url_for('super_admin.dashboard'))
        elif role == 'developer':
            return redirect(url_for('developer.dashboard'))
        return redirect(url_for('feed.newsfeed'))

    return render_template('landing.html', user_id=None, username=None)
