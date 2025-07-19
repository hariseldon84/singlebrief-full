"""
Main API router for v1 endpoints
"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, organizations, teams

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])