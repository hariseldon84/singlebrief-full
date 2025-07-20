"""
Pydantic schemas for orchestrator API
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class QueryPriority(int, Enum):
    """Query priority levels"""
    LOW = 1
    NORMAL = 5
    HIGH = 7
    URGENT = 9
    CRITICAL = 10


class ProcessingStatusEnum(str, Enum):
    """Query processing status"""
    PENDING = "pending"
    PARSING = "parsing"
    ROUTING = "routing"
    PROCESSING = "processing"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"


# Request Schemas
class QueryRequest(BaseModel):
    """Schema for intelligence query requests"""
    query: str = Field(
        ..., 
        description="Natural language query", 
        min_length=1, 
        max_length=2000,
        example="What is my team working on today?"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Additional context for the query",
        example={"session_id": "sess_123", "source": "web_ui"}
    )
    priority: QueryPriority = Field(
        default=QueryPriority.NORMAL, 
        description="Query priority level"
    )
    async_processing: bool = Field(
        default=False, 
        description="Whether to process asynchronously"
    )
    include_sources: bool = Field(
        default=True, 
        description="Include source attribution in response"
    )
    response_format: str = Field(
        default="detailed",
        description="Response format preference",
        pattern="^(brief|detailed|executive)$"
    )

    class Config:
        schema_extra = {
            "example": {
                "query": "What are the current blockers for my team?",
                "context": {
                    "session_id": "sess_abc123",
                    "source": "web_ui"
                },
                "priority": 5,
                "async_processing": False,
                "include_sources": True,
                "response_format": "detailed"
            }
        }


class BatchQueryRequest(BaseModel):
    """Schema for batch query processing"""
    queries: List[QueryRequest] = Field(
        ...,
        description="List of queries to process",
        max_items=10
    )
    batch_priority: QueryPriority = Field(
        default=QueryPriority.NORMAL,
        description="Priority for the entire batch"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "queries": [
                    {
                        "query": "Team status update",
                        "priority": 5
                    },
                    {
                        "query": "Project milestone progress",
                        "priority": 7
                    }
                ],
                "batch_priority": 5
            }
        }


class DailyBriefRequest(BaseModel):
    """Schema for daily brief generation"""
    include_metrics: bool = Field(default=True, description="Include performance metrics")
    include_sentiment: bool = Field(default=True, description="Include team sentiment analysis")
    time_range_hours: int = Field(default=24, ge=1, le=168, description="Time range in hours")
    custom_sections: List[str] = Field(default_factory=list, description="Custom sections to include")
    
    class Config:
        schema_extra = {
            "example": {
                "include_metrics": True,
                "include_sentiment": True,
                "time_range_hours": 24,
                "custom_sections": ["team_updates", "project_progress"]
            }
        }


# Response Schemas
class SourceInfo(BaseModel):
    """Schema for source information"""
    module: str = Field(..., description="Source module name")
    type: str = Field(..., description="Source type (slack, email, etc.)")
    name: str = Field(..., description="Source name or identifier")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Source confidence score")
    timestamp: Optional[datetime] = Field(None, description="When data was collected")


class QueryResponse(BaseModel):
    """Schema for query response"""
    query_id: str = Field(..., description="Unique query identifier")
    status: ProcessingStatusEnum = Field(..., description="Processing status")
    response: Optional[str] = Field(None, description="Generated response text")
    confidence_score: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=1.0, 
        description="Overall confidence in the response"
    )
    sources: List[SourceInfo] = Field(
        default_factory=list, 
        description="Information sources used"
    )
    processing_time_ms: int = Field(
        default=0, 
        ge=0, 
        description="Processing time in milliseconds"
    )
    modules_used: List[str] = Field(
        default_factory=list, 
        description="Orchestrator modules involved"
    )
    error_message: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Additional response metadata"
    )
    task_id: Optional[str] = Field(None, description="Task ID for async processing")
    key_insights: List[str] = Field(
        default_factory=list,
        description="Key insights extracted from the response"
    )
    action_items: List[str] = Field(
        default_factory=list,
        description="Recommended action items"
    )

    class Config:
        schema_extra = {
            "example": {
                "query_id": "query_abc123",
                "status": "completed",
                "response": "Your team is currently working on 3 major initiatives...",
                "confidence_score": 0.92,
                "sources": [
                    {
                        "module": "team_comms_crawler",
                        "type": "slack",
                        "name": "Engineering Channel",
                        "confidence": 0.95
                    }
                ],
                "processing_time_ms": 1234,
                "modules_used": ["team_comms_crawler", "memory_engine"],
                "key_insights": ["Team velocity increased 15%", "2 blockers identified"],
                "action_items": ["Review sprint capacity", "Address API performance"]
            }
        }


class TaskStatusResponse(BaseModel):
    """Schema for async task status"""
    task_id: str = Field(..., description="Task identifier")
    status: str = Field(..., description="Task status")
    result: Optional[QueryResponse] = Field(None, description="Task result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    progress: Optional[float] = Field(None, ge=0.0, le=1.0, description="Completion progress")
    estimated_completion_seconds: Optional[int] = Field(None, description="Estimated time to completion")
    created_at: datetime = Field(..., description="Task creation time")
    updated_at: datetime = Field(..., description="Last update time")


class ModuleInfo(BaseModel):
    """Schema for module information"""
    name: str = Field(..., description="Module name")
    capabilities: List[str] = Field(..., description="Module capabilities")
    status: str = Field(..., description="Module status")
    available: bool = Field(..., description="Whether module is available")
    last_health_check: Optional[datetime] = Field(None, description="Last health check time")
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")


class HealthStatusResponse(BaseModel):
    """Schema for health status"""
    orchestrator_status: str = Field(..., description="Overall orchestrator status")
    modules: Dict[str, ModuleInfo] = Field(..., description="Module status information")
    timestamp: datetime = Field(..., description="Health check timestamp")
    uptime_seconds: int = Field(..., ge=0, description="System uptime in seconds")
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="System performance metrics")
    
    class Config:
        schema_extra = {
            "example": {
                "orchestrator_status": "healthy",
                "modules": {
                    "team_comms_crawler": {
                        "name": "team_comms_crawler",
                        "capabilities": ["team_communication", "slack_data"],
                        "status": "healthy",
                        "available": True
                    }
                },
                "timestamp": "2024-01-15T10:30:00Z",
                "uptime_seconds": 86400
            }
        }


class StatisticsResponse(BaseModel):
    """Schema for orchestrator statistics"""
    total_queries_processed: int = Field(..., ge=0, description="Total queries processed")
    queries_today: int = Field(..., ge=0, description="Queries processed today")
    average_response_time_ms: float = Field(..., ge=0, description="Average response time")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Success rate")
    active_modules: int = Field(..., ge=0, description="Number of active modules")
    daily_briefs_generated: int = Field(..., ge=0, description="Daily briefs generated")
    user_queries_this_week: int = Field(..., ge=0, description="User queries this week")
    most_common_query_types: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most common query types with counts"
    )
    performance_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Performance percentiles"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "total_queries_processed": 15847,
                "queries_today": 234,
                "average_response_time_ms": 1678.5,
                "success_rate": 0.987,
                "active_modules": 4,
                "daily_briefs_generated": 156,
                "user_queries_this_week": 45,
                "most_common_query_types": [
                    {"type": "team_status", "count": 89},
                    {"type": "project_update", "count": 67}
                ],
                "performance_metrics": {
                    "p50_response_time_ms": 1200.0,
                    "p95_response_time_ms": 3400.0,
                    "p99_response_time_ms": 5600.0
                }
            }
        }


class BatchProcessingResponse(BaseModel):
    """Schema for batch processing response"""
    batch_id: str = Field(..., description="Batch processing identifier")
    total_queries: int = Field(..., ge=0, description="Total queries in batch")
    task_id: str = Field(..., description="Celery task ID")
    estimated_completion_seconds: int = Field(..., ge=0, description="Estimated completion time")
    status: str = Field(..., description="Batch processing status")
    
    class Config:
        schema_extra = {
            "example": {
                "batch_id": "batch_abc123",
                "total_queries": 5,
                "task_id": "celery_task_xyz789",
                "estimated_completion_seconds": 60,
                "status": "processing"
            }
        }