"""
CubePermutation AI - FastAPI Application Gateway
================================================
High-performance REST API gateway for the CubePermutation AI Flutter Mobile App.
Connects directly to the existing MySQL database and OpenCV/Kociemba algorithmic pipelines.

Runs alongside or independent of the Flask MVC web server.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.db import init_database
from fastapi_app.routers import (
    auth_routes, card_routes, cube_routes, profile_routes,
)

app = FastAPI(
    title="CubePermutation AI Mobile API",
    description="FastAPI Backend for CubePermutation AI Cross-Platform Flutter Mobile Client",
    version="1.0.0"
)

# Cross-Origin Resource Sharing - explicit allow-list only.
# A wildcard + credentials would let any web page call this API with the
# victim's session cookie; enumerate real front-end origins instead
# (override with CORS_ALLOW_ORIGINS=https://a.example,https://b.example).
def _allowed_origins():
    raw = os.environ.get("CORS_ALLOW_ORIGINS", "")
    if raw.strip():
        return [o.strip() for o in raw.split(",") if o.strip()]
    return [
        "http://127.0.0.1:5050",
        "http://localhost:5050",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to ensure MySQL tables are created and seeded
@app.on_event("startup")
def startup_db():
    init_database()

# Include Feature Routers
app.include_router(auth_routes)
app.include_router(cube_routes)
app.include_router(profile_routes)
app.include_router(card_routes.router)

@app.get("/health")
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "CubePermutation AI FastAPI Backend",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fastapi_app.main:app", host="127.0.0.1", port=8000, reload=True)
