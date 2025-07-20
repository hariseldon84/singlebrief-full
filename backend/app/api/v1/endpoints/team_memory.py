"""API endpoints for team memory and collaboration management."""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_async_session
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.ai.team_collaboration import team_collaboration_service

router = APIRouter()


class TeamMemoryCreateRequest(BaseModel):
    """Request model for creating team memory."""
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    memory_type: str = Field(..., description="Type: team_process, decision_pattern, collaboration_style, project_context")
    category: str = Field(..., min_length=1, max_length=100)
    metadata: Optional[Dict[str, Any]] = None
    visibility: str = Field(default="team", description="Visibility: team, organization, private")
    access_level: str = Field(default="read_write", description="Access: read_only, read_write, admin_only")


class TeamMemoryValidationRequest(BaseModel):
    """Request model for validating team memory."""
    is_valid: bool = Field(..., description="Whether the memory is considered valid")


class MemoryPermissionsUpdateRequest(BaseModel):
    """Request model for updating memory permissions."""
    visibility: Optional[str] = Field(None, description="New visibility level")
    access_level: Optional[str] = Field(None, description="New access level")


class CrossTeamSharingRequest(BaseModel):
    """Request model for cross-team memory sharing."""
    target_team_id: str = Field(..., description="ID of the team to share with")
    sharing_permissions: Dict[str, Any] = Field(..., description="Sharing permissions and controls")


class TeamMemoryResponse(BaseModel):
    """Response model for team memory."""
    id: str
    title: str
    content: str
    memory_type: str
    category: str
    importance_score: float
    relevance_score: float
    consensus_level: float
    consensus_status: str
    validated_by_count: int
    visibility: str
    access_level: str
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]


class TeamInteractionAnalysisResponse(BaseModel):
    """Response model for team interaction analysis."""
    team_id: str
    analysis_timestamp: str
    communication_frequency: Dict[str, Any]
    participation_patterns: Dict[str, Any]
    collaboration_effectiveness: Dict[str, Any]
    knowledge_sharing: Dict[str, Any]
    decision_patterns: Dict[str, Any]
    team_health_indicators: Dict[str, Any]


@router.post("/teams/{team_id}/memories", response_model=Dict[str, str])
async def create_team_memory(
    team_id: str,
    request: TeamMemoryCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, str]:
    """
    Create a new team memory.
    
    Creates a shared memory item for the team that can be validated
    by team members and used for collaborative context building.
    """
    try:
        team_collaboration_service.session = session
        memory_id = await team_collaboration_service.create_team_memory(
            team_id=team_id,
            created_by_user_id=current_user.id,
            title=request.title,
            content=request.content,
            memory_type=request.memory_type,
            category=request.category,
            metadata=request.metadata,
            visibility=request.visibility,
            access_level=request.access_level
        )
        
        return {"memory_id": memory_id, "message": "Team memory created successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create team memory: {str(e)}"
        )


@router.get("/teams/{team_id}/memories", response_model=List[TeamMemoryResponse])
async def get_team_memories(
    team_id: str,
    category: Optional[str] = Query(None, description="Filter by category"),
    memory_type: Optional[str] = Query(None, description="Filter by memory type"),
    min_consensus: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum consensus level"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of memories to return"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> List[TeamMemoryResponse]:
    """
    Get team memories with role-based filtering.
    
    Returns team memories that the current user has access to,
    based on their role and the memory access levels.
    """
    try:
        team_collaboration_service.session = session
        memories = await team_collaboration_service.get_team_memories(
            team_id=team_id,
            user_id=current_user.id,
            category=category,
            memory_type=memory_type,
            min_consensus=min_consensus,
            limit=limit
        )
        
        return [TeamMemoryResponse(**memory) for memory in memories]
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve team memories: {str(e)}"
        )


@router.post("/memories/{memory_id}/validate", response_model=Dict[str, Any])
async def validate_team_memory(
    memory_id: str,
    request: TeamMemoryValidationRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Validate a team memory.
    
    Allows team members to validate or invalidate team memories,
    contributing to consensus building and memory quality.
    """
    try:
        team_collaboration_service.session = session
        validation_result = await team_collaboration_service.validate_team_memory(
            memory_id=memory_id,
            validating_user_id=current_user.id,
            is_valid=request.is_valid
        )
        
        return validation_result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate team memory: {str(e)}"
        )


@router.get("/teams/{team_id}/analysis", response_model=TeamInteractionAnalysisResponse)
async def analyze_team_interactions(
    team_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> TeamInteractionAnalysisResponse:
    """
    Analyze team interaction patterns and collaboration dynamics.
    
    Provides insights into team communication, participation,
    knowledge sharing, and overall team health indicators.
    """
    try:
        team_collaboration_service.session = session
        analysis = await team_collaboration_service.analyze_team_interaction_patterns(team_id)
        
        from datetime import datetime, timezone
        return TeamInteractionAnalysisResponse(
            team_id=team_id,
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
            communication_frequency=analysis["communication_frequency"],
            participation_patterns=analysis["participation_patterns"],
            collaboration_effectiveness=analysis["collaboration_effectiveness"],
            knowledge_sharing=analysis["knowledge_sharing"],
            decision_patterns=analysis["decision_patterns"],
            team_health_indicators=analysis["team_health_indicators"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze team interactions: {str(e)}"
        )


@router.put("/memories/{memory_id}/permissions", response_model=Dict[str, Any])
async def update_memory_permissions(
    memory_id: str,
    request: MemoryPermissionsUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Update memory permissions (team leads and admins only).
    
    Allows team leads and admins to modify visibility and
    access levels for team memories.
    """
    try:
        team_collaboration_service.session = session
        result = await team_collaboration_service.update_memory_permissions(
            memory_id=memory_id,
            user_id=current_user.id,
            new_visibility=request.visibility,
            new_access_level=request.access_level
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update memory permissions: {str(e)}"
        )


@router.post("/teams/{source_team_id}/memories/{memory_id}/share", response_model=Dict[str, Any])
async def share_memory_across_teams(
    source_team_id: str,
    memory_id: str,
    request: CrossTeamSharingRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Share a team memory with another team.
    
    Enables cross-team knowledge sharing with appropriate
    permissions and access controls.
    """
    try:
        team_collaboration_service.session = session
        sharing_result = await team_collaboration_service.cross_team_memory_sharing(
            source_team_id=source_team_id,
            target_team_id=request.target_team_id,
            memory_id=memory_id,
            requesting_user_id=current_user.id,
            sharing_permissions=request.sharing_permissions
        )
        
        return sharing_result
        
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to share memory across teams: {str(e)}"
        )


@router.get("/teams/{team_id}/health", response_model=Dict[str, Any])
async def get_team_health_indicators(
    team_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get team health indicators and collaboration metrics.
    
    Provides a quick overview of team collaboration health,
    consensus levels, and participation patterns.
    """
    try:
        team_collaboration_service.session = session
        analysis = await team_collaboration_service.analyze_team_interaction_patterns(team_id)
        
        # Return just the health indicators
        return analysis["team_health_indicators"]
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get team health indicators: {str(e)}"
        )


@router.get("/teams/{team_id}/memories/categories", response_model=List[Dict[str, Any]])
async def get_memory_categories(
    team_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> List[Dict[str, Any]]:
    """
    Get available memory categories for the team.
    
    Returns categories of team memories along with counts
    and consensus levels for organizational purposes.
    """
    try:
        team_collaboration_service.session = session
        memories = await team_collaboration_service.get_team_memories(
            team_id=team_id,
            user_id=current_user.id,
            limit=1000  # Get all memories for category analysis
        )
        
        # Organize by category
        categories = {}
        for memory in memories:
            category = memory["category"]
            if category not in categories:
                categories[category] = {
                    "category": category,
                    "count": 0,
                    "average_consensus": 0.0,
                    "memory_types": set()
                }
            
            categories[category]["count"] += 1
            categories[category]["average_consensus"] += memory["consensus_level"]
            categories[category]["memory_types"].add(memory["memory_type"])
        
        # Calculate averages and convert sets to lists
        result = []
        for category_data in categories.values():
            category_data["average_consensus"] /= category_data["count"]
            category_data["memory_types"] = list(category_data["memory_types"])
            result.append(category_data)
        
        return sorted(result, key=lambda x: x["count"], reverse=True)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get memory categories: {str(e)}"
        )