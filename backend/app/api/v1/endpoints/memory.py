"""
Memory API endpoints for SingleBrief AI system
Handles memory operations, context retrieval, and lifecycle management
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.context_retrieval import context_retrieval_service
from app.ai.memory_lifecycle import memory_lifecycle_manager
from app.ai.memory_service import memory_service
from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.auth import User

router = APIRouter()

# Request/Response Models

class MemorySearchRequest(BaseModel):
    query: str = Field(..., description="Search query for memory retrieval")
    memory_types: Optional[List[str]] = Field(
        None, description="Filter by memory types"
    )
    categories: Optional[List[str]] = Field(None, description="Filter by categories")
    limit: int = Field(10, ge=1, le=50, description="Maximum results to return")
    min_similarity: float = Field(
        0.7, ge=0.0, le=1.0, description="Minimum similarity threshold"
    )

class ContextRetrievalRequest(BaseModel):
    query: str = Field(..., description="Query for context retrieval")
    session_id: Optional[str] = Field(None, description="Current session ID to exclude")
    max_memories: int = Field(
        10, ge=1, le=20, description="Maximum memories to retrieve"
    )
    max_conversations: int = Field(
        3, ge=1, le=10, description="Maximum conversations to retrieve"
    )
    max_decisions: int = Field(
        5, ge=1, le=10, description="Maximum decisions to retrieve"
    )
    time_window_days: int = Field(
        30, ge=1, le=365, description="Time window for context retrieval"
    )

class MemoryLifecycleRequest(BaseModel):
    operation: str = Field(
        ..., description="Lifecycle operation: expiration, optimization, cleanup"
    )
    organization_id: Optional[str] = Field(
        None, description="Organization ID for scoped operations"
    )
    dry_run: bool = Field(False, description="Whether to perform a dry run")

class CreateUserMemoryRequest(BaseModel):
    memory_type: str = Field(..., description="Type of memory")
    category: str = Field(..., description="Memory category")
    content: str = Field(..., description="Memory content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    importance_score: float = Field(0.5, ge=0.0, le=1.0, description="Importance score")
    confidence_level: float = Field(0.5, ge=0.0, le=1.0, description="Confidence level")
    source: str = Field("api", description="Memory source")

@router.post("/search", response_model=Dict[str, Any])
async def search_memories(
    request: MemorySearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search for relevant memories using semantic similarity"""
    try:
        results = await memory_service.search_memories(
            query=request.query,
            user_id=current_user.id,
            memory_types=request.memory_types,
            categories=request.categories,
            limit=request.limit,
            min_similarity=request.min_similarity,
        )

        return {
            "query": request.query,
            "user_id": current_user.id,
            "results": results,
            "count": len(results),
            "filters": {
                "memory_types": request.memory_types,
                "categories": request.categories,
                "min_similarity": request.min_similarity,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Memory search failed: {str(e)}")

@router.post("/context", response_model=Dict[str, Any])
async def get_context(
    request: ContextRetrievalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve comprehensive cross-session context for a query"""
    try:
        context = await context_retrieval_service.get_cross_session_context(
            db=db,
            user_id=current_user.id,
            query=request.query,
            session_id=request.session_id,
            max_memories=request.max_memories,
            max_conversations=request.max_conversations,
            max_decisions=request.max_decisions,
            time_window_days=request.time_window_days,
        )

        return context

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Context retrieval failed: {str(e)}"
        )

@router.post("/contextual-search", response_model=Dict[str, Any])
async def contextual_memory_search(
    query: str = Body(..., embed=True),
    context_filters: Optional[Dict[str, Any]] = Body(None, embed=True),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Enhanced memory search with contextual filtering"""
    try:
        results = await context_retrieval_service.get_contextual_memory_search(
            db=db,
            user_id=current_user.id,
            query=query,
            context_filters=context_filters,
            limit=limit,
        )

        return results

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Contextual search failed: {str(e)}"
        )

@router.post("/create", response_model=Dict[str, Any])
async def create_user_memory(
    request: CreateUserMemoryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new user memory with vector embedding"""
    try:
        memory = await memory_service.create_user_memory(
            db=db,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            memory_type=request.memory_type,
            category=request.category,
            content=request.content,
            metadata=request.metadata,
            importance_score=request.importance_score,
            confidence_level=request.confidence_level,
            source=request.source,
        )

        return {
            "memory_id": memory.id,
            "created_at": memory.created_at.isoformat(),
            "message": "Memory created successfully",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Memory creation failed: {str(e)}")

@router.post("/lifecycle", response_model=Dict[str, Any])
async def manage_memory_lifecycle(
    request: MemoryLifecycleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manage memory lifecycle operations"""
    try:
        # Use current user's organization if not specified and user is not admin
        org_id = request.organization_id
        if not org_id and hasattr(current_user, "organization_id"):
            org_id = current_user.organization_id

        if request.operation == "expiration":
            result = await memory_lifecycle_manager.apply_expiration_policies(
                db=db, organization_id=org_id, dry_run=request.dry_run
            )
        elif request.operation == "optimization":
            result = await memory_lifecycle_manager.optimize_memory_storage(
                db=db, organization_id=org_id
            )
        elif request.operation == "cleanup":
            result = await memory_lifecycle_manager.cleanup_orphaned_embeddings(
                db=db, organization_id=org_id
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown lifecycle operation: {request.operation}",
            )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Lifecycle management failed: {str(e)}"
        )

@router.get("/usage-report", response_model=Dict[str, Any])
async def get_memory_usage_report(
    organization_id: Optional[str] = Query(
        None, description="Organization ID for scoped report"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate comprehensive memory usage report"""
    try:
        # Use current user's organization if not specified
        org_id = organization_id
        if not org_id and hasattr(current_user, "organization_id"):
            org_id = current_user.organization_id

        report = await memory_lifecycle_manager.generate_memory_usage_report(
            db=db, organization_id=org_id
        )

        return report

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Usage report generation failed: {str(e)}"
        )

@router.get("/conversation-context/{user_id}", response_model=Dict[str, Any])
async def get_conversation_context(
    user_id: str,
    query: str = Query(..., description="Query for context generation"),
    max_items: int = Query(5, ge=1, le=20, description="Maximum context items"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get relevant conversation context for a user query"""
    try:
        # Check if current user can access the requested user's context
        if current_user.id != user_id and not hasattr(current_user, "is_admin"):
            raise HTTPException(status_code=403, detail="Access denied to user context")

        context = await memory_service.get_conversation_context(
            db=db, user_id=user_id, query=query, max_items=max_items
        )

        return context

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Context generation failed: {str(e)}"
        )

@router.get("/analytics", response_model=Dict[str, Any])
async def get_memory_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days for analysis"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get memory analytics and patterns for the current user"""
    try:
        analytics = await memory_service.analyze_memory_patterns(
            db=db, user_id=current_user.id, days=days
        )

        return analytics

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Analytics generation failed: {str(e)}"
        )

@router.delete("/memory/{memory_id}", response_model=Dict[str, Any])
async def delete_memory(
    memory_id: str,
    memory_type: str = Query(
        ..., description="Memory type: user_memory or team_memory"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a memory and its associated embedding"""
    try:
        success = await memory_service.delete_memory_embedding(
            db=db, memory_id=memory_id, memory_type=memory_type
        )

        if success:
            return {"memory_id": memory_id, "message": "Memory deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Memory not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Memory deletion failed: {str(e)}")

@router.put("/memory/{memory_id}", response_model=Dict[str, Any])
async def update_memory_embedding(
    memory_id: str,
    memory_type: str = Query(
        ..., description="Memory type: user_memory or team_memory"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update vector embedding for a memory"""
    try:
        success = await memory_service.update_memory_embedding(
            db=db, memory_id=memory_id, memory_type=memory_type
        )

        if success:
            return {
                "memory_id": memory_id,
                "message": "Memory embedding updated successfully",
            }
        else:
            raise HTTPException(status_code=404, detail="Memory not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Memory update failed: {str(e)}")

@router.get("/health", response_model=Dict[str, Any])
async def memory_system_health():
    """Check memory system health and status"""
    try:
        # Initialize memory service
        memory_initialized = await memory_service.initialize()

        return {
            "status": "healthy" if memory_initialized else "degraded",
            "memory_service": "initialized" if memory_initialized else "failed",
            "vector_database": memory_service.vector_db.database_type,
            "timestamp": memory_service.__class__.__name__,
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": memory_service.__class__.__name__,
        }
