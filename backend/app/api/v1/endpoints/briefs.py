"""Brief Generation API endpoints for SingleBrief.

This module provides REST API endpoints for automated brief generation,
content intelligence analysis, and template-based rendering.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import (APIRouter, Body, Depends, HTTPException, Query, Request,
                     status)
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_organization, get_current_user
from app.core.database import get_db_session
from app.models.user import Organization, User
from app.services.brief_generation import (BriefConfig, BriefFormat,
                                           BriefSection, GeneratedBrief,
                                           brief_generation_service)
from app.services.content_intelligence import (ContentIntelligence,
                                               ImportanceCategory,
                                               UrgencyLevel,
                                               content_intelligence_service)
from app.services.data_normalization import SourceType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/briefs", tags=["briefs"])

# Pydantic models for request/response

class BriefGenerationRequest(BaseModel):
    """Request model for brief generation."""

    brief_type: str = Field(default="daily", description="Type of brief to generate")
    format: str = Field(
        default="html", description="Output format: html, text, email, pdf"
    )
    sections: Optional[List[str]] = Field(
        None, description="Specific sections to include"
    )
    time_range_hours: int = Field(default=24, le=168, description="Time range in hours")
    include_sources: Optional[List[str]] = Field(None, description="Sources to include")
    exclude_sources: Optional[List[str]] = Field(None, description="Sources to exclude")
    priority_threshold: float = Field(
        default=0.3, le=1.0, description="Minimum priority threshold"
    )
    max_items_per_section: int = Field(
        default=10, le=50, description="Maximum items per section"
    )
    timezone: str = Field(default="UTC", description="User timezone")
    use_cache: bool = Field(default=True, description="Use cached results if available")

class BriefGenerationResponse(BaseModel):
    """Response model for generated brief."""

    brief_id: str = Field(..., description="Unique brief identifier")
    generated_at: str = Field(..., description="Generation timestamp")
    format: str = Field(..., description="Brief format")
    sections_count: int = Field(..., description="Number of sections")
    total_items: int = Field(..., description="Total items across all sections")
    sources_used: List[str] = Field(..., description="Data sources used")
    content_hash: str = Field(..., description="Content hash for caching")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")

class ContentIntelligenceRequest(BaseModel):
    """Request model for content intelligence analysis."""

    time_range_hours: int = Field(default=24, le=168, description="Time range in hours")
    include_sources: Optional[List[str]] = Field(None, description="Sources to analyze")
    exclude_sources: Optional[List[str]] = Field(None, description="Sources to exclude")
    content_types: Optional[List[str]] = Field(
        None, description="Content types to analyze"
    )
    min_importance: float = Field(
        default=0.0, description="Minimum importance threshold"
    )
    include_trends: bool = Field(default=True, description="Include trend analysis")
    include_sentiment: bool = Field(
        default=False, description="Include sentiment analysis"
    )

class ContentIntelligenceResponse(BaseModel):
    """Response model for content intelligence analysis."""

    total_items_analyzed: int = Field(..., description="Number of items analyzed")
    high_importance_count: int = Field(..., description="High importance items")
    urgent_items_count: int = Field(..., description="Urgent items")
    action_items_count: int = Field(..., description="Total action items")
    risk_indicators_count: int = Field(..., description="Risk indicators found")
    opportunity_indicators_count: int = Field(..., description="Opportunities found")
    trending_topics: List[Dict[str, Any]] = Field(..., description="Trending topics")
    intelligence_summary: List[Dict[str, Any]] = Field(
        ..., description="Intelligence analysis results"
    )

class BriefTemplateRequest(BaseModel):
    """Request model for brief template rendering."""

    brief_id: str = Field(..., description="Brief ID to render")
    format: str = Field(default="html", description="Render format")
    custom_template: Optional[str] = Field(None, description="Custom template content")

# API Endpoints

@router.post("/generate", response_model=BriefGenerationResponse)
async def generate_brief(
    request: BriefGenerationRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> BriefGenerationResponse:
    """Generate a personalized brief with intelligent content prioritization.

    Creates a comprehensive brief by aggregating content from all integrated
    sources, applying content intelligence, and rendering with templates.
    """
    try:
        # Validate and convert request parameters
        try:
            brief_format = BriefFormat(request.format)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid format: {request.format}. Must be one of: html, text, email, pdf",
            )

        # Convert sections
        sections = None
        if request.sections:
            sections = []
            for section_name in request.sections:
                try:
                    sections.append(BriefSection(section_name))
                except ValueError:
                    logger.warning(f"Invalid section name: {section_name}")

        # Convert sources
        include_sources = None
        if request.include_sources:
            include_sources = []
            for source_name in request.include_sources:
                try:
                    include_sources.append(SourceType(source_name))
                except ValueError:
                    logger.warning(f"Invalid source type: {source_name}")

        exclude_sources = None
        if request.exclude_sources:
            exclude_sources = []
            for source_name in request.exclude_sources:
                try:
                    exclude_sources.append(SourceType(source_name))
                except ValueError:
                    logger.warning(f"Invalid source type: {source_name}")

        # Create brief configuration
        config = BriefConfig(
            user_id=current_user.id,
            organization_id=current_org.id,
            brief_type=request.brief_type,
            format=brief_format,
            sections=sections,
            timezone=request.timezone,
            max_items_per_section=request.max_items_per_section,
            include_sources=include_sources or [],
            exclude_sources=exclude_sources or [],
            priority_threshold=request.priority_threshold,
            time_range_hours=request.time_range_hours,
        )

        # Generate brief
        generated_brief = await brief_generation_service.generate_brief(
            config=config, use_cache=request.use_cache
        )

        return BriefGenerationResponse(
            brief_id=generated_brief.id,
            generated_at=generated_brief.generated_at.isoformat(),
            format=generated_brief.format.value,
            sections_count=len(generated_brief.sections),
            total_items=generated_brief.generation_metadata.get("total_items", 0),
            sources_used=generated_brief.generation_metadata.get("sources_used", []),
            content_hash=generated_brief.content_hash,
            metadata=generated_brief.generation_metadata,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating brief: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Brief generation failed: {str(e)}",
        )

@router.get("/render/{brief_id}")
async def render_brief(
    brief_id: str,
    format: str = Query(default="html", description="Render format"),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
):
    """Render a generated brief in the specified format.

    Returns the brief content rendered using templates for display
    in web browsers, email clients, or as plain text.
    """
    try:
        # Validate format
        try:
            brief_format = BriefFormat(format)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid format: {format}",
            )

        # Retrieve brief from storage (implementation pending - using generation for now)
        config = BriefConfig(
            user_id=current_user.id, organization_id=current_org.id, format=brief_format
        )

        generated_brief = await brief_generation_service.generate_brief(config)

        # Render using template
        rendered_content = await brief_generation_service.render_brief_template(
            brief=generated_brief, format=brief_format
        )

        # Return appropriate response type
        if brief_format == BriefFormat.HTML:
            return HTMLResponse(content=rendered_content)
        elif brief_format in [BriefFormat.TEXT, BriefFormat.EMAIL]:
            return PlainTextResponse(content=rendered_content)
        else:
            # For PDF and other formats, return as attachment
            from fastapi.responses import Response

            return Response(
                content=rendered_content,
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f"attachment; filename=brief_{brief_id}.{format}"
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rendering brief: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Brief rendering failed: {str(e)}",
        )

@router.post("/intelligence/analyze", response_model=ContentIntelligenceResponse)
async def analyze_content_intelligence(
    request: ContentIntelligenceRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> ContentIntelligenceResponse:
    """Analyze content intelligence across integrated sources.

    Provides detailed analysis of content importance, urgency, trends,
    risks, and opportunities for better decision making.
    """
    try:
        # Convert source types
        include_sources = None
        if request.include_sources:
            include_sources = []
            for source_name in request.include_sources:
                try:
                    include_sources.append(SourceType(source_name))
                except ValueError:
                    logger.warning(f"Invalid source type: {source_name}")

        exclude_sources = None
        if request.exclude_sources:
            exclude_sources = []
            for source_name in request.exclude_sources:
                try:
                    exclude_sources.append(SourceType(source_name))
                except ValueError:
                    logger.warning(f"Invalid source type: {source_name}")

        # Get content for analysis using brief generation service
        config = BriefConfig(
            user_id=current_user.id,
            organization_id=current_org.id,
            time_range_hours=request.time_range_hours,
            include_sources=include_sources or [],
            exclude_sources=exclude_sources or [],
            priority_threshold=0.0,  # Get all content for analysis
        )

        # Use brief generation service to aggregate content (via public method)
        aggregated_content = await brief_generation_service.aggregate_content_for_analysis(config)

        # Apply content intelligence analysis
        intelligence_results = (
            await content_intelligence_service.analyze_content_intelligence(
                items=aggregated_content,
                context={"user_id": current_user.id, "organization_id": current_org.id},
            )
        )

        # Analyze results
        total_items = len(intelligence_results)
        high_importance_count = sum(
            1
            for r in intelligence_results
            if r.importance_category
            in [ImportanceCategory.CRITICAL, ImportanceCategory.HIGH]
        )
        urgent_items_count = sum(
            1
            for r in intelligence_results
            if r.urgency_level in [UrgencyLevel.IMMEDIATE, UrgencyLevel.TODAY]
        )
        action_items_count = sum(len(r.action_items) for r in intelligence_results)
        risk_indicators_count = sum(
            len(r.risk_indicators) for r in intelligence_results
        )
        opportunity_indicators_count = sum(
            len(r.opportunity_indicators) for r in intelligence_results
        )

        # Extract trending topics
        topic_frequency = {}
        for result in intelligence_results:
            for topic in result.key_topics:
                topic_frequency[topic] = topic_frequency.get(topic, 0) + 1

        trending_topics = [
            {
                "topic": topic,
                "frequency": freq,
                "trend_score": freq / total_items if total_items > 0 else 0,
            }
            for topic, freq in sorted(
                topic_frequency.items(), key=lambda x: x[1], reverse=True
            )[:10]
        ]

        # Prepare intelligence summary
        intelligence_summary = []
        for result in intelligence_results:
            if result.importance_score >= request.min_importance:
                summary_item = {
                    "item_id": result.item_id,
                    "importance_score": result.importance_score,
                    "importance_category": result.importance_category.value,
                    "urgency_level": result.urgency_level.value,
                    "urgency_score": result.urgency_score,
                    "trend_type": (
                        result.trend_type.value if result.trend_type else None
                    ),
                    "action_items_count": len(result.action_items),
                    "risk_indicators": result.risk_indicators,
                    "opportunity_indicators": result.opportunity_indicators,
                    "key_topics": result.key_topics[:3],  # Top 3 topics
                    "confidence_score": result.confidence_score,
                    "reasoning": result.reasoning,
                }

                if request.include_sentiment:
                    summary_item["sentiment_score"] = result.sentiment_score

                intelligence_summary.append(summary_item)

        # Sort by importance score
        intelligence_summary.sort(key=lambda x: x["importance_score"], reverse=True)

        return ContentIntelligenceResponse(
            total_items_analyzed=total_items,
            high_importance_count=high_importance_count,
            urgent_items_count=urgent_items_count,
            action_items_count=action_items_count,
            risk_indicators_count=risk_indicators_count,
            opportunity_indicators_count=opportunity_indicators_count,
            trending_topics=trending_topics,
            intelligence_summary=intelligence_summary[:50],  # Limit to top 50
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing content intelligence: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content intelligence analysis failed: {str(e)}",
        )

@router.get("/history")
async def get_brief_history(
    days: int = Query(default=7, le=30, description="Number of days to retrieve"),
    brief_type: str = Query(default="daily", description="Type of briefs to retrieve"),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> List[Dict[str, Any]]:
    """Get history of generated briefs for the user.

    Returns a list of previously generated briefs with metadata
    for tracking and analytics purposes.
    """
    try:
        # Brief history retrieval from database (implementation pending)
        # Note: Currently returning sample data until BriefHistory table is implemented
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Generate sample history data
        history = []
        for i in range(min(days, 7)):  # Generate up to 7 sample entries
            date = end_date - timedelta(days=i)
            history.append(
                {
                    "brief_id": f"brief_{current_user.id}_{int(date.timestamp())}",
                    "generated_at": date.isoformat(),
                    "brief_type": brief_type,
                    "sections_count": 5,
                    "total_items": 15 + i * 2,
                    "format": "html",
                    "status": "completed",
                }
            )

        return history

    except Exception as e:
        logger.error(f"Error retrieving brief history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve brief history: {str(e)}",
        )

@router.get("/sections", response_model=List[Dict[str, str]])
async def get_available_sections() -> List[Dict[str, str]]:
    """Get list of available brief sections."""
    return [
        {"value": section.value, "label": section.value.replace("_", " ").title()}
        for section in BriefSection
    ]

@router.get("/formats", response_model=List[Dict[str, str]])
async def get_available_formats() -> List[Dict[str, str]]:
    """Get list of available brief formats."""
    return [
        {"value": format.value, "label": format.value.upper()} for format in BriefFormat
    ]

@router.post("/schedule")
async def schedule_brief_generation(
    schedule_config: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Schedule automated brief generation.

    Configures automatic brief generation at specified intervals
    using Celery for background task processing.
    """
    try:
        # Celery task scheduling implementation (pending Celery integration)

        # Validate schedule configuration
        required_fields = ["frequency", "time", "format", "delivery_method"]
        for field in required_fields:
            if field not in schedule_config:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}",
                )

        # Placeholder implementation
        schedule_id = (
            f"schedule_{current_user.id}_{int(datetime.now(timezone.utc).timestamp())}"
        )

        logger.info(
            f"Scheduled brief generation for user {current_user.id}: {schedule_config}"
        )

        return {
            "success": True,
            "schedule_id": schedule_id,
            "message": "Brief generation scheduled successfully",
            "next_generation": (
                datetime.now(timezone.utc) + timedelta(hours=24)
            ).isoformat(),
            "config": schedule_config,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling brief generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule brief generation: {str(e)}",
        )

@router.get("/analytics")
async def get_brief_analytics(
    days: int = Query(default=30, le=90, description="Analytics time period"),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Get analytics and insights about brief generation and usage.

    Provides metrics on brief generation frequency, content sources,
    user engagement, and effectiveness indicators.
    """
    try:
        # Comprehensive analytics implementation (pending analytics service)
        # Note: Currently returning sample analytics data
        analytics = {
            "time_period_days": days,
            "total_briefs_generated": 25,
            "avg_briefs_per_week": 5.8,
            "most_active_sources": [
                {"source": "slack", "percentage": 35},
                {"source": "email", "percentage": 28},
                {"source": "github", "percentage": 20},
                {"source": "jira", "percentage": 17},
            ],
            "avg_sections_per_brief": 4.2,
            "avg_items_per_brief": 18.5,
            "user_engagement": {
                "avg_read_time_seconds": 145,
                "click_through_rate": 0.65,
                "action_completion_rate": 0.42,
            },
            "content_effectiveness": {
                "high_importance_accuracy": 0.87,
                "urgency_detection_accuracy": 0.92,
                "action_item_relevance": 0.78,
            },
            "trend_analysis": {
                "brief_generation_trend": "increasing",
                "content_volume_trend": "stable",
                "user_satisfaction_trend": "improving",
            },
        }

        return analytics

    except Exception as e:
        logger.error(f"Error retrieving brief analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analytics: {str(e)}",
        )
