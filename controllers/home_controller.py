"""
CubePermutation AI - Home & Landing Controller (MVC Pattern)
============================================================
Handles high-graphical landing page with interactive math diagrams,
feature overviews, and group theory introduction.
"""

from flask import Blueprint, render_template, session

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def index():
    """
    High-Graphic Landing Page:
    Application introduction, Group Theory visualization preview,
    and interactive 3D particle banner.
    """
    user_id = session.get('user_id')
    username = session.get('username')
    return render_template('landing.html', user_id=user_id, username=username)
