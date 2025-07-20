"""Search and Data Normalization API endpoints for SingleBrief.

This module provides REST API endpoints for unified search across all
integrated data sources, data normalization, and content management.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import (APIRouter, Body, Depends, HTTPException, Query, Request,
                     status)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_organization, get_current_user
from app.core.database import get_db_session
from app.models.user import Organization, User
from app.services.data_normalization import (ContentType, SourceType,
                                             UnifiedDataItem,
                                             data_normalization_service)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])

# Pydantic models for request/response

class SearchRequest(BaseModel):
    """Request model for unified search."""

    query: str = Field(..., description="Search query text")
    content_types: Optional[List[str]] = Field(
        None, description="Filter by content types"
    )
    source_types: Optional[List[str]] = Field(
        None, description="Filter by source types"
    )
    start_date: Optional[datetime] = Field(None, description="Start date filter")
    end_date: Optional[datetime] = Field(None, description="End date filter")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    categories: Optional[List[str]] = Field(None, description="Filter by categories")
    limit: int = Field(default=50, le=200, description="Maximum results to return")
    offset: int = Field(default=0, description="Offset for pagination")
    include_highlights: bool = Field(
        default=True, description="Include search highlights"
    )
    sort_by: str = Field(
        default="relevance", description="Sort order: relevance, date, score"
    )

class SearchResponse(BaseModel):
    """Response model for search results."""

    total: int = Field(..., description="Total number of results")
    items: List[Dict[str, Any]] = Field(..., description="Search result items")
    offset: int = Field(..., description="Current offset")
    limit: int = Field(..., description="Results per page")
    query: str = Field(..., description="Original query")
    facets: Optional[Dict[str, Any]] = Field(None, description="Search facets")
    suggestions: Optional[List[str]] = Field(None, description="Query suggestions")

class NormalizationRequest(BaseModel):
    """Request model for data normalization."""

    source_type: str = Field(..., description="Source system type")
    raw_data: Dict[str, Any] = Field(..., description="Raw data to normalize")
    auto_classify: bool = Field(
        default=True, description="Automatically classify content"
    )
    auto_index: bool = Field(default=True, description="Automatically index to search")

class NormalizationResponse(BaseModel):
    """Response model for data normalization."""

    success: bool = Field(..., description="Whether normalization succeeded")
    normalized_item: Dict[str, Any] = Field(..., description="Normalized data item")
    classification: Dict[str, Any] = Field(..., description="Content classification")
    duplicates: List[str] = Field(default=[], description="Detected duplicate IDs")

class BulkNormalizationRequest(BaseModel):
    """Request model for bulk data normalization."""

    source_type: str = Field(..., description="Source system type")
    raw_data_items: List[Dict[str, Any]] = Field(
        ..., description="Raw data items to normalize"
    )
    batch_size: int = Field(default=100, le=500, description="Processing batch size")
    auto_classify: bool = Field(
        default=True, description="Automatically classify content"
    )
    auto_index: bool = Field(default=True, description="Automatically index to search")
    detect_duplicates: bool = Field(
        default=True, description="Detect and mark duplicates"
    )

class StatsRequest(BaseModel):
    """Request model for getting search statistics."""

    include_content_types: bool = Field(
        default=True, description="Include content type breakdown"
    )
    include_sources: bool = Field(default=True, description="Include source breakdown")
    include_activity: bool = Field(default=True, description="Include recent activity")
    include_quality: bool = Field(default=False, description="Include quality metrics")
    time_period_days: int = Field(
        default=30, le=365, description="Time period for activity stats"
    )

class ReindexRequest(BaseModel):
    """Request model for reindexing data."""

    source_types: Optional[List[str]] = Field(
        None, description="Source types to reindex"
    )
    content_types: Optional[List[str]] = Field(
        None, description="Content types to reindex"
    )
    full_reindex: bool = Field(default=False, description="Perform full reindex")
    cleanup_stale: bool = Field(default=True, description="Clean up stale data")

# API Endpoints

@router.post("/query", response_model=SearchResponse)
async def search_unified_data(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> SearchResponse:
    """Search across all integrated data sources with unified results.

    Performs full-text search across normalized data from all integrated
    sources including Slack, email, documents, GitHub, and Jira.
    """
    try:
        # Convert string enums to enum objects
        content_types = None
        if request.content_types:
            content_types = []
            for ct in request.content_types:
                try:
                    content_types.append(ContentType(ct))
                except ValueError:
                    logger.warning(f"Invalid content type: {ct}")

        source_types = None
        if request.source_types:
            source_types = []
            for st in request.source_types:
                try:
                    source_types.append(SourceType(st))
                except ValueError:
                    logger.warning(f"Invalid source type: {st}")

        # Build date range
        date_range = None
        if request.start_date and request.end_date:
            date_range = (request.start_date, request.end_date)
        elif request.start_date:
            date_range = (request.start_date, datetime.now(timezone.utc))
        elif request.end_date:
            # Default to 1 year back if only end date provided
            start_date = request.end_date - timedelta(days=365)
            date_range = (start_date, request.end_date)

        # Perform search
        results = await data_normalization_service.search_unified_data(
            query=request.query,
            content_types=content_types,
            source_types=source_types,
            date_range=date_range,
            tags=request.tags,
            categories=request.categories,
            limit=request.limit,
            offset=request.offset,
        )

        # TODO: Add facets and suggestions
        facets = None
        suggestions = None

        return SearchResponse(
            total=results.get("total", 0),
            items=results.get("items", []),
            offset=request.offset,
            limit=request.limit,
            query=request.query,
            facets=facets,
            suggestions=suggestions,
        )

    except Exception as e:
        logger.error(f"Error performing search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )

@router.post("/normalize", response_model=NormalizationResponse)
async def normalize_data_item(
    request: NormalizationRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> NormalizationResponse:
    """Normalize a single data item to the unified schema.

    Converts raw data from external sources into the unified data format
    with automatic content classification and optional search indexing.
    """
    try:
        # Validate source type
        try:
            source_type = SourceType(request.source_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid source type: {request.source_type}",
            )

        # Normalize based on source type
        normalized_item = None
        if source_type == SourceType.SLACK:
            normalized_item = await data_normalization_service.normalize_slack_data(
                request.raw_data
            )
        elif source_type in [SourceType.GMAIL, SourceType.OUTLOOK]:
            normalized_item = await data_normalization_service.normalize_email_data(
                request.raw_data
            )
        elif source_type in [SourceType.GDRIVE, SourceType.ONEDRIVE]:
            normalized_item = await data_normalization_service.normalize_document_data(
                request.raw_data
            )
        elif source_type == SourceType.GITHUB:
            normalized_item = await data_normalization_service.normalize_github_data(
                request.raw_data
            )
        elif source_type == SourceType.JIRA:
            normalized_item = await data_normalization_service.normalize_jira_data(
                request.raw_data
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Normalization not implemented for source type: {request.source_type}",
            )

        # Detect duplicates
        duplicates = []
        if normalized_item:
            duplicate_results = await data_normalization_service.detect_duplicates(
                [normalized_item]
            )
            for original_id, duplicate_ids in duplicate_results.items():
                if normalized_item.id in duplicate_ids:
                    duplicates.extend(
                        [original_id]
                        + [d for d in duplicate_ids if d != normalized_item.id]
                    )

        # Index to search engine if requested
        if request.auto_index and normalized_item:
            await data_normalization_service.index_to_search_engine([normalized_item])

        # Prepare classification info
        classification = {
            "content_type": (
                normalized_item.content_type.value if normalized_item else "unknown"
            ),
            "categories": normalized_item.categories if normalized_item else [],
            "tags": normalized_item.tags if normalized_item else [],
            "confidence": (
                normalized_item.classification_confidence if normalized_item else 0.0
            ),
        }

        return NormalizationResponse(
            success=True,
            normalized_item=normalized_item.to_dict() if normalized_item else {},
            classification=classification,
            duplicates=duplicates,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error normalizing data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Normalization failed: {str(e)}",
        )

@router.post("/normalize-bulk", response_model=Dict[str, Any])
async def normalize_bulk_data(
    request: BulkNormalizationRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Normalize multiple data items in bulk with batch processing.

    Efficiently processes large amounts of raw data with automatic
    deduplication, classification, and search indexing.
    """
    try:
        # Validate source type
        try:
            source_type = SourceType(request.source_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid source type: {request.source_type}",
            )

        # Process items in batches
        total_items = len(request.raw_data_items)
        processed_items = []
        failed_items = []
        duplicate_groups = {}

        for i in range(0, total_items, request.batch_size):
            batch = request.raw_data_items[i : i + request.batch_size]
            batch_normalized = []

            # Normalize each item in the batch
            for raw_item in batch:
                try:
                    # Normalize based on source type
                    normalized_item = None
                    if source_type == SourceType.SLACK:
                        normalized_item = (
                            await data_normalization_service.normalize_slack_data(
                                raw_item
                            )
                        )
                    elif source_type in [SourceType.GMAIL, SourceType.OUTLOOK]:
                        normalized_item = (
                            await data_normalization_service.normalize_email_data(
                                raw_item
                            )
                        )
                    elif source_type in [SourceType.GDRIVE, SourceType.ONEDRIVE]:
                        normalized_item = (
                            await data_normalization_service.normalize_document_data(
                                raw_item
                            )
                        )
                    elif source_type == SourceType.GITHUB:
                        normalized_item = (
                            await data_normalization_service.normalize_github_data(
                                raw_item
                            )
                        )
                    elif source_type == SourceType.JIRA:
                        normalized_item = (
                            await data_normalization_service.normalize_jira_data(
                                raw_item
                            )
                        )

                    if normalized_item:
                        batch_normalized.append(normalized_item)
                        processed_items.append(normalized_item.id)

                except Exception as e:
                    logger.error(f"Error normalizing batch item: {e}")
                    failed_items.append({"error": str(e), "item": raw_item})

            # Detect duplicates within batch
            if request.detect_duplicates and batch_normalized:
                batch_duplicates = await data_normalization_service.detect_duplicates(
                    batch_normalized
                )
                duplicate_groups.update(batch_duplicates)

            # Index batch to search engine
            if request.auto_index and batch_normalized:
                await data_normalization_service.index_to_search_engine(
                    batch_normalized
                )

            logger.info(
                f"Processed batch {i // request.batch_size + 1}/{(total_items + request.batch_size - 1) // request.batch_size}"
            )

        return {
            "success": True,
            "total_items": total_items,
            "processed_count": len(processed_items),
            "failed_count": len(failed_items),
            "duplicate_groups": duplicate_groups,
            "failed_items": failed_items[:10],  # Return first 10 failures
            "processing_summary": {
                "batches_processed": (total_items + request.batch_size - 1)
                // request.batch_size,
                "batch_size": request.batch_size,
                "source_type": request.source_type,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk normalization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk normalization failed: {str(e)}",
        )

@router.get("/stats", response_model=Dict[str, Any])
async def get_search_statistics(
    request: StatsRequest = Depends(),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Get comprehensive statistics about indexed data and search performance.

    Returns aggregated statistics including content type distribution,
    source breakdown, activity trends, and quality metrics.
    """
    try:
        # Get aggregated statistics from search engine
        stats = await data_normalization_service.get_aggregated_stats()

        # Add organization-specific metadata
        stats["organization_id"] = current_org.id
        stats["generated_at"] = datetime.now(timezone.utc).isoformat()
        stats["time_period_days"] = request.time_period_days

        # Filter stats based on request preferences
        if not request.include_content_types:
            stats.pop("content_types", None)
        if not request.include_sources:
            stats.pop("source_types", None)
        if not request.include_activity:
            stats.pop("recent_activity", None)

        # Add quality metrics if requested
        if request.include_quality:
            stats["quality_metrics"] = {
                "avg_freshness_score": 0.75,  # Placeholder
                "avg_quality_score": 0.68,  # Placeholder
                "classification_confidence": 0.82,  # Placeholder
            }

        return stats

    except Exception as e:
        logger.error(f"Error getting search statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}",
        )

@router.post("/reindex", response_model=Dict[str, Any])
async def reindex_data(
    request: ReindexRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Reindex data from integrated sources to refresh the search index.

    Rebuilds the search index with fresh data from all or selected
    integration sources with optional cleanup of stale data.
    """
    try:
        # Check user permissions (admin only for full reindex)
        if request.full_reindex:
            # TODO: Add proper admin permission check
            logger.info(f"Full reindex requested by user {current_user.id}")

        reindex_results = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "full_reindex": request.full_reindex,
            "source_types": request.source_types,
            "content_types": request.content_types,
            "cleanup_performed": False,
            "cleanup_count": 0,
        }

        # Clean up stale data first if requested
        if request.cleanup_stale:
            cleanup_count = await data_normalization_service.cleanup_stale_data()
            reindex_results["cleanup_performed"] = True
            reindex_results["cleanup_count"] = cleanup_count

        # Perform reindexing
        if request.full_reindex:
            success = await data_normalization_service.reindex_all_data()
            reindex_results["success"] = success
            reindex_results["message"] = (
                "Full reindex completed" if success else "Full reindex failed"
            )
        else:
            # Selective reindexing based on source/content types
            reindex_results["success"] = True
            reindex_results["message"] = (
                "Selective reindex completed (placeholder implementation)"
            )

        reindex_results["completed_at"] = datetime.now(timezone.utc).isoformat()
        return reindex_results

    except Exception as e:
        logger.error(f"Error reindexing data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reindexing failed: {str(e)}",
        )

@router.get("/content-types", response_model=List[Dict[str, str]])
async def get_content_types() -> List[Dict[str, str]]:
    """Get list of available content types for filtering."""
    return [
        {"value": ct.value, "label": ct.value.replace("_", " ").title()}
        for ct in ContentType
    ]

@router.get("/source-types", response_model=List[Dict[str, str]])
async def get_source_types() -> List[Dict[str, str]]:
    """Get list of available source types for filtering."""
    return [
        {"value": st.value, "label": st.value.replace("_", " ").title()}
        for st in SourceType
    ]

@router.get("/health", response_model=Dict[str, Any])
async def get_search_health() -> Dict[str, Any]:
    """Get health status of the search and data normalization system."""
    try:
        # Check Elasticsearch connectivity
        import aiohttp

        search_healthy = False
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{data_normalization_service.elasticsearch_url}/_cluster/health"
                ) as response:
                    if response.status == 200:
                        cluster_health = await response.json()
                        search_healthy = cluster_health.get("status") in [
                            "green",
                            "yellow",
                        ]
        except Exception:
            pass

        return {
            "status": "healthy" if search_healthy else "degraded",
            "search_engine": {
                "connected": search_healthy,
                "url": data_normalization_service.elasticsearch_url,
                "index": data_normalization_service.search_index,
            },
            "data_normalization": {
                "available": True,
                "supported_sources": [
                    st.value for st in SourceType if st != SourceType.UNKNOWN
                ],
                "supported_content_types": [
                    ct.value for ct in ContentType if ct != ContentType.UNKNOWN
                ],
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Error checking search health: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
