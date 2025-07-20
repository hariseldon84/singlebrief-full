"""
Orchestrator API endpoints
Intelligence query processing and management endpoints
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from fastapi.responses import StreamingResponse

from app.auth.dependencies import get_current_user
from app.orchestrator.core import OrchestratorAgent, QueryContext, QueryType, ProcessingStatus
from app.schemas.orchestrator import (
    QueryRequest,
    QueryResponse, 
    TaskStatusResponse,
    HealthStatusResponse,
    DailyBriefRequest,
    BatchQueryRequest,
    BatchProcessingResponse,
    StatisticsResponse
)
from app.tasks.intelligence_tasks import (
    process_query, 
    process_urgent_query, 
    process_daily_brief,
    get_task_status,
    health_check_all_modules
)
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)
router = APIRouter()

# Singleton orchestrator instance
_orchestrator: Optional[OrchestratorAgent] = None


def get_orchestrator() -> OrchestratorAgent:
    """Get or create orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent()
    return _orchestrator


# Endpoints
@router.post("/query", response_model=QueryResponse)
async def process_intelligence_query(
    request: QueryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> QueryResponse:
    """
    Process an intelligence query.
    
    Supports both synchronous and asynchronous processing.
    """
    try:
        logger.info(f"Processing query from user {current_user['id']}: {request.query[:50]}...")
        
        # Create query context
        context = QueryContext(
            user_id=current_user['id'],
            organization_id=current_user.get('organization_id', ''),
            team_id=current_user.get('team_id'),
            session_id=request.context.get('session_id', ''),
            priority=request.priority,
            metadata=request.context
        )
        
        if request.async_processing:
            # Process asynchronously using Celery
            task_func = process_urgent_query if request.priority >= 8 else process_query
            
            context_data = {
                'query_id': context.query_id,
                'user_id': context.user_id,
                'organization_id': context.organization_id,
                'team_id': context.team_id,
                'session_id': context.session_id,
                'metadata': context.metadata
            }
            
            task = task_func.delay(request.query, context_data)
            
            return QueryResponse(
                query_id=context.query_id,
                status="processing",
                task_id=task.id,
                metadata={
                    "async_processing": True,
                    "estimated_completion_seconds": 30 if request.priority >= 8 else 60
                }
            )
        
        else:
            # Process synchronously
            orchestrator = get_orchestrator()
            result = await orchestrator.process_query(request.query, context)
            
            return QueryResponse(
                query_id=result.query_id,
                status=result.status.value,
                response=result.response,
                confidence_score=result.confidence_score,
                sources=result.sources if request.include_sources else [],
                processing_time_ms=result.processing_time_ms,
                modules_used=result.modules_used,
                error_message=result.error_message,
                metadata=result.metadata
            )
            
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {str(e)}"
        )


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_query_task_status(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> TaskStatusResponse:
    """Get status of an asynchronous query task"""
    try:
        result = celery_app.AsyncResult(task_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return TaskStatusResponse(
            task_id=task_id,
            status=result.status,
            result=result.result if result.ready() else None,
            error=result.traceback if result.failed() else None,
            created_at=datetime.now(timezone.utc),  # Placeholder
            updated_at=datetime.now(timezone.utc)
        )
        
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.post("/briefs/daily", response_model=QueryResponse)
async def generate_daily_brief(
    request: DailyBriefRequest = DailyBriefRequest(),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> QueryResponse:
    """Generate daily intelligence brief for the current user"""
    try:
        logger.info(f"Generating daily brief for user {current_user['id']}")
        
        task = process_daily_brief.delay(
            user_id=current_user['id'],
            organization_id=current_user.get('organization_id', ''),
            team_id=current_user.get('team_id')
        )
        
        return QueryResponse(
            query_id=f"daily_brief_{current_user['id']}_{datetime.now().strftime('%Y%m%d')}",
            status="processing",
            task_id=task.id,
            metadata={
                "brief_type": "daily",
                "async_processing": True,
                "estimated_completion_seconds": 45
            }
        )
        
    except Exception as e:
        logger.error(f"Daily brief generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Daily brief generation failed: {str(e)}"
        )


@router.get("/health", response_model=HealthStatusResponse)
async def get_orchestrator_health() -> HealthStatusResponse:
    """Get health status of orchestrator and all modules"""
    try:
        orchestrator = get_orchestrator()
        health_status = await orchestrator.get_health_status()
        
        return HealthStatusResponse(
            orchestrator_status=health_status.get('orchestrator', 'unknown'),
            modules=health_status.get('modules', {}),
            timestamp=datetime.now(timezone.utc),
            uptime_seconds=health_status.get('uptime_seconds', 0)
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.post("/health/check")
async def trigger_health_check(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Trigger comprehensive health check (async)"""
    try:
        task = health_check_all_modules.delay()
        
        return {
            "message": "Health check initiated",
            "task_id": task.id,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Health check initiation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check initiation failed: {str(e)}"
        )


@router.get("/modules")
async def get_available_modules(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get list of available orchestrator modules"""
    try:
        orchestrator = get_orchestrator()
        modules = orchestrator.module_registry.get_registered_modules()
        
        module_info = {}
        for module_name in modules:
            module = orchestrator.module_registry.get_module(module_name)
            if module:
                module_info[module_name] = {
                    "name": module.name,
                    "capabilities": module.capabilities,
                    "available": orchestrator.module_registry.is_module_available(module_name)
                }
        
        return {
            "modules": module_info,
            "total_modules": len(modules),
            "available_modules": len([m for m in module_info.values() if m["available"]])
        }
        
    except Exception as e:
        logger.error(f"Failed to get modules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get modules: {str(e)}"
        )


@router.get("/queries/recent")
async def get_recent_queries(
    limit: int = 10,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get recent queries for the current user"""
    try:
        # In a real implementation, this would query the database
        # For now, returning mock data
        
        recent_queries = [
            {
                "query_id": f"query_{i}",
                "query": f"Sample query {i}",
                "status": "completed" if i % 3 != 0 else "processing",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "processing_time_ms": 1500 + (i * 100)
            }
            for i in range(1, limit + 1)
        ]
        
        return {
            "queries": recent_queries,
            "total": len(recent_queries),
            "user_id": current_user['id']
        }
        
    except Exception as e:
        logger.error(f"Failed to get recent queries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent queries: {str(e)}"
        )


@router.post("/queries/batch", response_model=BatchProcessingResponse)
async def process_batch_queries(
    request: BatchQueryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> BatchProcessingResponse:
    """Process multiple queries in batch"""
    try:
        queries = request.queries
        if len(queries) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 queries per batch"
            )
        
        logger.info(f"Processing batch of {len(queries)} queries for user {current_user['id']}")
        
        # Prepare batch data
        batch_data = []
        for query_req in queries:
            context_data = {
                'query_id': f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(batch_data)}",
                'user_id': current_user['id'],
                'organization_id': current_user.get('organization_id', ''),
                'team_id': current_user.get('team_id'),
                'session_id': query_req.context.get('session_id', ''),
                'metadata': query_req.context
            }
            
            batch_data.append({
                'query': query_req.query,
                'context': context_data,
                'priority': query_req.priority
            })
        
        # Import and use batch processing task
        from app.tasks.intelligence_tasks import batch_process_queries
        task = batch_process_queries.delay(batch_data)
        
        return BatchProcessingResponse(
            batch_id=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            total_queries=len(queries),
            task_id=task.id,
            estimated_completion_seconds=len(queries) * 10,
            status="processing"
        )
        
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch processing failed: {str(e)}"
        )


@router.get("/statistics", response_model=StatisticsResponse)
async def get_orchestrator_statistics(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> StatisticsResponse:
    """Get orchestrator usage statistics"""
    try:
        # Mock statistics - in real implementation, query from database/metrics
        stats = {
            "total_queries_processed": 15847,
            "queries_today": 234,
            "average_response_time_ms": 1678,
            "success_rate": 0.987,
            "active_modules": 4,
            "daily_briefs_generated": 156,
            "user_queries_this_week": 45,
            "most_common_query_types": [
                {"type": "team_status", "count": 89},
                {"type": "project_update", "count": 67},
                {"type": "daily_brief", "count": 45}
            ],
            "performance_metrics": {
                "p50_response_time_ms": 1200,
                "p95_response_time_ms": 3400,
                "p99_response_time_ms": 5600
            }
        }
        
        return StatisticsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )