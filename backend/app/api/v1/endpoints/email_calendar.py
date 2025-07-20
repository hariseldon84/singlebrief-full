"""Email and Calendar Integration API endpoints for SingleBrief.

This module provides REST API endpoints for Gmail/Outlook email and calendar
integration, OAuth flows, message retrieval, and calendar analysis.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import (APIRouter, Body, Depends, HTTPException, Query, Request,
                     status)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.integration_hub import integration_hub_service
from app.auth.dependencies import get_current_organization, get_current_user
from app.core.database import get_db_session
from app.integrations.email_calendar_integration import email_calendar_service
from app.models.user import Organization, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email-calendar", tags=["email-calendar"])

# Pydantic models for request/response

class EmailCalendarSetupRequest(BaseModel):
    """Request model for setting up email/calendar integration."""

    service_type: str = Field(..., description="Service type: gmail or outlook")
    client_id: str = Field(..., description="OAuth client ID")
    client_secret: str = Field(..., description="OAuth client secret")
    tenant_id: Optional[str] = Field(
        None, description="Microsoft tenant ID (Outlook only)"
    )
    sync_frequency: str = Field(default="hourly", description="Sync frequency")
    max_emails: int = Field(default=1000, description="Maximum emails per batch")
    include_attachments: bool = Field(default=False, description="Include attachments")
    calendar_lookback_days: int = Field(
        default=30, description="Calendar lookback days"
    )
    calendar_lookahead_days: int = Field(
        default=90, description="Calendar lookahead days"
    )

class EmailCalendarOAuthInitiateRequest(BaseModel):
    """Request model for initiating OAuth flow."""

    service_type: str = Field(..., description="Service type: gmail or outlook")
    redirect_uri: str = Field(..., description="OAuth redirect URI")
    state: Optional[str] = Field(None, description="CSRF protection state")

class EmailCalendarOAuthInitiateResponse(BaseModel):
    """Response model for OAuth initiation."""

    authorization_url: str = Field(..., description="URL for user authorization")
    state: str = Field(..., description="State parameter for verification")
    service_type: str = Field(..., description="Service type")

class EmailCalendarOAuthCompleteRequest(BaseModel):
    """Request model for completing OAuth flow."""

    service_type: str = Field(..., description="Service type: gmail or outlook")
    code: str = Field(..., description="Authorization code")
    redirect_uri: str = Field(..., description="OAuth redirect URI")

class EmailCalendarOAuthCompleteResponse(BaseModel):
    """Response model for OAuth completion."""

    success: bool = Field(..., description="Whether OAuth was successful")
    token_id: str = Field(..., description="Created OAuth token ID")
    service_type: str = Field(..., description="Service type")
    user_email: str = Field(..., description="Connected user email")

class EmailQuery(BaseModel):
    """Query parameters for fetching emails."""

    service_type: str = Field(..., description="Service type: gmail or outlook")
    query: Optional[str] = Field(None, description="Search query")
    max_results: int = Field(default=100, le=1000, description="Maximum emails")
    include_body: bool = Field(default=True, description="Include email body")

class CalendarQuery(BaseModel):
    """Query parameters for fetching calendar events."""

    service_type: str = Field(..., description="Service type: gmail or outlook")
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    calendar_id: Optional[str] = Field(None, description="Specific calendar ID")

class ThreadAnalysisRequest(BaseModel):
    """Request model for email thread analysis."""

    service_type: str = Field(..., description="Service type: gmail or outlook")
    thread_id: str = Field(..., description="Thread/conversation ID")

# API Endpoints

@router.post("/setup", response_model=Dict[str, Any])
async def setup_email_calendar_integration(
    request: EmailCalendarSetupRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Set up email/calendar integration for the organization.

    This endpoint configures the email/calendar connector and creates the
    integration configuration for the organization.
    """
    try:
        # Validate service type
        if request.service_type not in ["gmail", "outlook"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service type must be 'gmail' or 'outlook'",
            )

        # Register connector if not already registered
        try:
            connector_id = (
                await email_calendar_service.register_email_calendar_connector(
                    request.service_type
                )
            )
        except Exception:
            # Connector might already exist
            connector_id = "existing"

        # Create integration configuration
        installation_config = {
            "client_id": request.client_id,
            "client_secret": request.client_secret,
            "sync_frequency": request.sync_frequency,
            "max_emails": request.max_emails,
            "include_attachments": request.include_attachments,
            "calendar_lookback_days": request.calendar_lookback_days,
            "calendar_lookahead_days": request.calendar_lookahead_days,
        }

        if request.service_type == "outlook" and request.tenant_id:
            installation_config["tenant_id"] = request.tenant_id

        # Create integration record
        from app.models.integration import Integration

        integration = Integration(
            organization_id=current_org.id,
            configured_by_user_id=current_user.id,
            service_type=request.service_type,
            service_name=f"{request.service_type.title()} Email and Calendar",
            integration_key=f"{request.service_type}-{current_org.id}",
            config=installation_config,
            capabilities=[
                "read_emails",
                "read_calendar",
                "email_search",
                "thread_tracking",
                "contact_mapping",
                "priority_scoring",
            ],
            scopes=(
                email_calendar_service.gmail_scopes
                if request.service_type == "gmail"
                else email_calendar_service.outlook_scopes
            ),
            status="pending_auth",
        )

        session.add(integration)
        await session.commit()
        await session.refresh(integration)

        logger.info(
            f"{request.service_type} integration setup for organization {current_org.id}"
        )

        return {
            "success": True,
            "integration_id": integration.id,
            "service_type": request.service_type,
            "status": "configured",
            "message": f"{request.service_type.title()} integration configured. Complete OAuth to activate.",
            "next_step": "oauth_authorization",
        }

    except Exception as e:
        logger.error(f"Error setting up {request.service_type} integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup {request.service_type} integration: {str(e)}",
        )

@router.post("/oauth/initiate", response_model=EmailCalendarOAuthInitiateResponse)
async def initiate_email_calendar_oauth(
    request: EmailCalendarOAuthInitiateRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> EmailCalendarOAuthInitiateResponse:
    """Initiate OAuth 2.0 authorization flow for email/calendar access.

    Returns the authorization URL that the user should visit to grant
    permissions to their email and calendar.
    """
    try:
        authorization_url = await email_calendar_service.initiate_oauth_flow(
            organization_id=current_org.id,
            user_id=current_user.id,
            service_type=request.service_type,
            redirect_uri=request.redirect_uri,
            state=request.state,
        )

        # Extract state from URL if not provided
        from urllib.parse import parse_qs, urlparse

        if not request.state:
            parsed_url = urlparse(authorization_url)
            query_params = parse_qs(parsed_url.query)
            state = query_params.get("state", [""])[0]
        else:
            state = request.state

        return EmailCalendarOAuthInitiateResponse(
            authorization_url=authorization_url,
            state=state,
            service_type=request.service_type,
        )

    except Exception as e:
        logger.error(f"Error initiating {request.service_type} OAuth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate OAuth: {str(e)}",
        )

@router.post("/oauth/complete", response_model=EmailCalendarOAuthCompleteResponse)
async def complete_email_calendar_oauth(
    request: EmailCalendarOAuthCompleteRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> EmailCalendarOAuthCompleteResponse:
    """Complete OAuth 2.0 authorization flow for email/calendar access.

    Exchanges the authorization code for access tokens and stores them
    securely for the organization.
    """
    try:
        oauth_token = await email_calendar_service.complete_oauth_flow(
            organization_id=current_org.id,
            user_id=current_user.id,
            service_type=request.service_type,
            authorization_code=request.code,
            redirect_uri=request.redirect_uri,
        )

        return EmailCalendarOAuthCompleteResponse(
            success=True,
            token_id=oauth_token.id,
            service_type=request.service_type,
            user_email=oauth_token.external_email or "Unknown",
        )

    except Exception as e:
        logger.error(f"Error completing {request.service_type} OAuth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete OAuth: {str(e)}",
        )

@router.post("/emails", response_model=List[Dict[str, Any]])
async def fetch_emails(
    query: EmailQuery,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> List[Dict[str, Any]]:
    """Fetch emails from Gmail or Outlook.

    Returns emails from the specified service with optional search filtering
    and body content inclusion.
    """
    try:
        # Get the organization's integration
        from sqlalchemy import and_, select

        from app.models.integration import Integration

        integration_query = select(Integration).where(
            and_(
                Integration.organization_id == current_org.id,
                Integration.service_type == query.service_type,
                Integration.status == "active",
            )
        )
        result = await session.execute(integration_query)
        integration = result.scalar_one_or_none()

        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active {query.service_type} integration found",
            )

        # Fetch emails from service
        emails = await email_calendar_service.fetch_emails(
            integration_id=integration.id,
            service_type=query.service_type,
            query=query.query,
            max_results=query.max_results,
            include_body=query.include_body,
        )

        return emails

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching emails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch emails: {str(e)}",
        )

@router.post("/calendar", response_model=List[Dict[str, Any]])
async def fetch_calendar_events(
    query: CalendarQuery,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> List[Dict[str, Any]]:
    """Fetch calendar events from Google Calendar or Outlook Calendar.

    Returns calendar events from the specified service within the given
    date range.
    """
    try:
        # Get the organization's integration
        from sqlalchemy import and_, select

        from app.models.integration import Integration

        integration_query = select(Integration).where(
            and_(
                Integration.organization_id == current_org.id,
                Integration.service_type == query.service_type,
                Integration.status == "active",
            )
        )
        result = await session.execute(integration_query)
        integration = result.scalar_one_or_none()

        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active {query.service_type} integration found",
            )

        # Fetch calendar events from service
        events = await email_calendar_service.fetch_calendar_events(
            integration_id=integration.id,
            service_type=query.service_type,
            start_date=query.start_date,
            end_date=query.end_date,
            calendar_id=query.calendar_id,
        )

        return events

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching calendar events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch calendar events: {str(e)}",
        )

@router.post("/thread/analyze", response_model=Dict[str, Any])
async def analyze_email_thread(
    request: ThreadAnalysisRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Analyze email thread for context and relationships.

    Provides detailed analysis of an email thread including participants,
    topics, sentiment, and action items.
    """
    try:
        # Get the organization's integration
        from sqlalchemy import and_, select

        from app.models.integration import Integration

        integration_query = select(Integration).where(
            and_(
                Integration.organization_id == current_org.id,
                Integration.service_type == request.service_type,
                Integration.status == "active",
            )
        )
        result = await session.execute(integration_query)
        integration = result.scalar_one_or_none()

        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active {request.service_type} integration found",
            )

        # Analyze email thread
        analysis = await email_calendar_service.analyze_email_threads(
            integration_id=integration.id,
            service_type=request.service_type,
            thread_id=request.thread_id,
        )

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing email thread: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze thread: {str(e)}",
        )

@router.get("/contacts", response_model=List[Dict[str, Any]])
async def get_contacts_and_relationships(
    service_type: str = Query(..., description="Service type: gmail or outlook"),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> List[Dict[str, Any]]:
    """Extract contact information and relationship mapping.

    Analyzes email communications to extract contact relationships,
    communication frequency, and relationship strength scores.
    """
    try:
        # Get the organization's integration
        from sqlalchemy import and_, select

        from app.models.integration import Integration

        integration_query = select(Integration).where(
            and_(
                Integration.organization_id == current_org.id,
                Integration.service_type == service_type,
                Integration.status == "active",
            )
        )
        result = await session.execute(integration_query)
        integration = result.scalar_one_or_none()

        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active {service_type} integration found",
            )

        # Extract contacts and relationships
        contacts = await email_calendar_service.extract_contacts_and_relationships(
            integration_id=integration.id, service_type=service_type
        )

        return contacts

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting contacts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract contacts: {str(e)}",
        )

@router.get("/status", response_model=Dict[str, Any])
async def get_email_calendar_integration_status(
    service_type: str = Query(..., description="Service type: gmail or outlook"),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Get the status of email/calendar integration for the organization.

    Returns information about the integration status, connected account,
    and configuration details.
    """
    try:
        # Get the organization's integration
        from sqlalchemy import and_, select

        from app.models.integration import Integration

        integration_query = select(Integration).where(
            and_(
                Integration.organization_id == current_org.id,
                Integration.service_type == service_type,
            )
        )
        result = await session.execute(integration_query)
        integration = result.scalar_one_or_none()

        if not integration:
            return {
                "configured": False,
                "status": "not_configured",
                "service_type": service_type,
                "message": f"{service_type.title()} integration not configured",
            }

        # Get OAuth token status
        from app.models.integration import OAuthToken

        token_query = (
            select(OAuthToken)
            .where(OAuthToken.integration_id == integration.id)
            .order_by(OAuthToken.created_at.desc())
        )

        token_result = await session.execute(token_query)
        oauth_token = token_result.scalar_one_or_none()

        # Get data sources
        from app.models.integration import DataSource

        sources_query = select(DataSource).where(
            DataSource.integration_id == integration.id
        )
        sources_result = await session.execute(sources_query)
        data_sources = sources_result.scalars().all()

        email_sources = [ds for ds in data_sources if ds.source_type == "email"]
        calendar_sources = [ds for ds in data_sources if ds.source_type == "calendar"]

        return {
            "configured": True,
            "status": integration.status,
            "health_status": integration.health_status,
            "service_type": service_type,
            "connected_email": oauth_token.external_email if oauth_token else None,
            "connected_user": oauth_token.external_username if oauth_token else None,
            "email_sources": len(email_sources),
            "calendar_sources": len(calendar_sources),
            "last_sync": (
                integration.last_sync_at.isoformat()
                if integration.last_sync_at
                else None
            ),
            "sync_frequency": integration.config.get("sync_frequency", "hourly"),
            "max_emails": integration.config.get("max_emails", 1000),
            "include_attachments": integration.config.get("include_attachments", False),
        }

    except Exception as e:
        logger.error(f"Error getting {service_type} integration status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get integration status: {str(e)}",
        )
