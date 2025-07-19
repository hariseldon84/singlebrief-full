"""
Team management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db_session
from app.models.user import User, Team
from app.schemas.user import TeamResponse, TeamCreate, TeamUpdate
from app.auth.dependencies import get_current_active_user, require_manager

router = APIRouter()


@router.get("/", response_model=List[TeamResponse])
async def list_teams(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """List teams for current user"""
    try:
        # TODO: Implement proper team membership query
        teams = current_user.teams or []
        return [TeamResponse.from_orm(team) for team in teams]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch teams"
        )


@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new team (manager/admin only)"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be part of an organization"
        )
    
    try:
        team = Team(
            name=team_data.name,
            description=team_data.description,
            organization_id=current_user.organization_id,
            is_public=team_data.is_public
        )
        
        db.add(team)
        await db.commit()
        await db.refresh(team)
        
        # TODO: Add current user as team admin
        
        return TeamResponse.from_orm(team)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create team"
        )


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get team by ID"""
    try:
        result = await db.execute(select(Team).where(Team.id == team_id))
        team = result.scalar_one_or_none()
        
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        # TODO: Check if user has access to this team
        
        return TeamResponse.from_orm(team)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch team"
        )


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: str,
    team_update: TeamUpdate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db_session)
):
    """Update team (manager/admin only)"""
    try:
        result = await db.execute(select(Team).where(Team.id == team_id))
        team = result.scalar_one_or_none()
        
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        # TODO: Check if user can manage this team
        
        # Update team fields
        if team_update.name is not None:
            team.name = team_update.name
        if team_update.description is not None:
            team.description = team_update.description
        if team_update.is_public is not None:
            team.is_public = team_update.is_public
        
        await db.commit()
        await db.refresh(team)
        
        return TeamResponse.from_orm(team)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update team"
        )