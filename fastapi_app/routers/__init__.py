"""FastAPI Routers Package"""
from .auth_routes import router as auth_routes
from .cube_routes import router as cube_routes
from .profile_routes import router as profile_routes

__all__ = ["auth_routes", "cube_routes", "profile_routes"]
