"""API endpoints for user preference learning and management."""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_async_session
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.ai.preference_learning import preference_learning_service

router = APIRouter()


class PreferenceUpdateRequest(BaseModel):
    """Request model for manual preference updates."""
    category: str = Field(..., description="Preference category")
    key: str = Field(..., description="Preference key")
    value: Any = Field(..., description="Preference value")


class PreferenceAnalysisResponse(BaseModel):
    """Response model for preference analysis."""
    user_id: str
    analysis_timestamp: str
    communication_style: Dict[str, Any]
    topic_interests: Dict[str, Any]
    status: str = "success"


class UserPreferencesResponse(BaseModel):
    """Response model for user preferences."""
    user_id: str
    preferences: Dict[str, Dict[str, Any]]
    retrieved_at: str


@router.get("/analyze/{user_id}", response_model=PreferenceAnalysisResponse)
async def analyze_user_preferences(
    user_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> PreferenceAnalysisResponse:
    """
    Run comprehensive preference learning analysis for a user.
    
    This endpoint triggers analysis of the user's communication style,
    topic interests, and behavioral patterns to update their preferences.
    """
    # Verify user has permission to analyze preferences
    if current_user.id != user_id and not current_user.is_admin:
        # Check if current user is in same organization and has team lead role
        if (current_user.organization_id != await _get_user_organization(session, user_id) or 
            current_user.role not in ["team_lead", "admin"]):
            raise HTTPException(
                status_code=403, 
                detail="Not authorized to analyze this user's preferences"
            )
    
    try:
        # Run preference analysis
        preference_learning_service.session = session
        results = await preference_learning_service.run_preference_learning_analysis(user_id)
        
        return PreferenceAnalysisResponse(
            user_id=user_id,
            analysis_timestamp=results["analysis_timestamp"],
            communication_style=results["communication_style"],
            topic_interests=results["topic_interests"],
            status="success"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze user preferences: {str(e)}"
        )


@router.get("/", response_model=UserPreferencesResponse)
async def get_user_preferences(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> UserPreferencesResponse:
    """
    Get user preferences, optionally filtered by category.
    
    Returns all learned preferences for the current user,
    including confidence scores and evidence counts.
    """
    try:
        preference_learning_service.session = session
        preferences = await preference_learning_service.get_user_preferences(
            user_id=current_user.id,
            category=category
        )
        
        from datetime import datetime, timezone
        return UserPreferencesResponse(
            user_id=current_user.id,
            preferences=preferences,
            retrieved_at=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve user preferences: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserPreferencesResponse)
async def get_other_user_preferences(
    user_id: str,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> UserPreferencesResponse:
    """
    Get preferences for another user (team leads and admins only).
    
    Allows team leads to view preferences of their team members
    for better personalization of team communications.
    """
    # Verify user has permission
    if not current_user.is_admin:
        if (current_user.organization_id != await _get_user_organization(session, user_id) or 
            current_user.role != "team_lead"):
            raise HTTPException(
                status_code=403, 
                detail="Not authorized to view this user's preferences"
            )
    
    try:
        preference_learning_service.session = session
        preferences = await preference_learning_service.get_user_preferences(
            user_id=user_id,
            category=category
        )
        
        from datetime import datetime, timezone
        return UserPreferencesResponse(
            user_id=user_id,
            preferences=preferences,
            retrieved_at=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve user preferences: {str(e)}"
        )


@router.put("/", status_code=200)
async def update_preference_manually(
    request: PreferenceUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, str]:
    """
    Manually update a user preference.
    
    Allows users to explicitly set their preferences,
    which takes precedence over learned preferences.
    """
    try:
        preference_learning_service.session = session
        await preference_learning_service.update_preference_manually(
            user_id=current_user.id,
            category=request.category,
            key=request.key,
            value=request.value,
            organization_id=current_user.organization_id
        )
        
        return {"message": "Preference updated successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update preference: {str(e)}"
        )


@router.post("/analyze", response_model=PreferenceAnalysisResponse)
async def trigger_preference_analysis(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> PreferenceAnalysisResponse:
    """
    Trigger preference analysis for the current user.
    
    Analyzes recent conversations and interactions to update
    learned preferences and behavioral patterns.
    """
    try:
        preference_learning_service.session = session
        results = await preference_learning_service.run_preference_learning_analysis(
            current_user.id
        )
        
        return PreferenceAnalysisResponse(
            user_id=current_user.id,
            analysis_timestamp=results["analysis_timestamp"],
            communication_style=results["communication_style"],
            topic_interests=results["topic_interests"],
            status="success"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze preferences: {str(e)}"
        )


@router.get("/communication-style/", response_model=Dict[str, Any])
async def get_communication_style_analysis(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get detailed communication style analysis for the current user.
    
    Returns comprehensive analysis of communication patterns,
    formality levels, preferred response formats, etc.
    """
    try:
        preference_learning_service.session = session
        analysis = await preference_learning_service.analyze_communication_style(
            current_user.id
        )
        
        return analysis
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze communication style: {str(e)}"
        )


@router.get("/topic-interests/", response_model=Dict[str, Any])
async def get_topic_interests_analysis(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get detailed topic interests analysis for the current user.
    
    Returns analysis of topics the user is most interested in,
    engagement patterns, and topic preferences.
    """
    try:
        preference_learning_service.session = session
        analysis = await preference_learning_service.analyze_topic_interests(
            current_user.id
        )
        
        return analysis
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze topic interests: {str(e)}"
        )


async def _get_user_organization(session: AsyncSession, user_id: str) -> str:
    """Helper function to get user's organization ID."""
    from sqlalchemy import select
    
    query = select(User.organization_id).where(User.id == user_id)
    result = await session.execute(query)
    org_id = result.scalar_one_or_none()
    
    if not org_id:
        raise HTTPException(status_code=404, detail="User not found")
    
    return org_id