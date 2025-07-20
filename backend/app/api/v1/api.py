"""
Main API router for v1 endpoints
"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, organizations, teams, orchestrator, memory, preferences, team_memory, privacy, context_response

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(orchestrator.router, prefix="/orchestrator", tags=["intelligence"])
api_router.include_router(memory.router, prefix="/memory", tags=["memory"])
api_router.include_router(preferences.router, prefix="/preferences", tags=["preferences"])
api_router.include_router(team_memory.router, prefix="/team-memory", tags=["team-memory"])
api_router.include_router(privacy.router, prefix="/privacy", tags=["privacy"])
api_router.include_router(context_response.router, prefix="/context-response", tags=["context-response"])