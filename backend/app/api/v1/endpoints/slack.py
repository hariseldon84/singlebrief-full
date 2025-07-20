"""Slack Integration API endpoints for SingleBrief.

This module provides REST API endpoints for Slack workspace integration,
OAuth flows, message retrieval, and webhook handling.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import (APIRouter, Body, Depends, HTTPException, Query, Request,
                     status)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.integration_hub import integration_hub_service
from app.auth.dependencies import get_current_organization, get_current_user
from app.core.database import get_db_session
from app.integrations.slack_integration import slack_integration_service
from app.models.user import Organization, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/slack", tags=["slack"])

# Pydantic models for request/response

class SlackOAuthInitiateRequest(BaseModel):
    """Request model for initiating Slack OAuth flow."""

    redirect_uri: str = Field(..., description="OAuth redirect URI")
    state: Optional[str] = Field(None, description="CSRF protection state")

class SlackOAuthInitiateResponse(BaseModel):
    """Response model for OAuth initiation."""

    authorization_url: str = Field(..., description="URL for user to authorize")
    state: str = Field(..., description="State parameter for verification")

class SlackOAuthCompleteRequest(BaseModel):
    """Request model for completing Slack OAuth flow."""

    code: str = Field(..., description="Authorization code from Slack")
    state: Optional[str] = Field(None, description="State parameter from initiation")
    redirect_uri: str = Field(..., description="OAuth redirect URI")

class SlackOAuthCompleteResponse(BaseModel):
    """Response model for OAuth completion."""

    success: bool = Field(..., description="Whether OAuth was successful")
    token_id: str = Field(..., description="Created OAuth token ID")
    team_name: str = Field(..., description="Connected Slack team name")
    user_name: str = Field(..., description="Connected Slack user name")

class SlackIntegrationSetupRequest(BaseModel):
    """Request model for setting up Slack integration."""

    client_id: str = Field(..., description="Slack app client ID")
    client_secret: str = Field(..., description="Slack app client secret")
    signing_secret: str = Field(..., description="Slack app signing secret")
    channels: Optional[List[str]] = Field(
        default=[], description="Specific channels to monitor"
    )
    keywords: Optional[List[str]] = Field(default=[], description="Keywords for alerts")
    sync_frequency: str = Field(default="realtime", description="Sync frequency")
    include_files: bool = Field(default=True, description="Include file attachments")
    include_reactions: bool = Field(
        default=True, description="Include message reactions"
    )
    thread_depth: int = Field(default=50, description="Maximum thread depth")

class SlackChannelResponse(BaseModel):
    """Response model for Slack channel information."""

    id: str = Field(..., description="Channel ID")
    name: str = Field(..., description="Channel name")
    is_private: bool = Field(..., description="Whether channel is private")
    is_archived: bool = Field(..., description="Whether channel is archived")
    member_count: int = Field(..., description="Number of members")
    purpose: Optional[str] = Field(None, description="Channel purpose")
    topic: Optional[str] = Field(None, description="Channel topic")

class SlackMessageQuery(BaseModel):
    """Query parameters for fetching Slack messages."""

    channel_id: str = Field(..., description="Slack channel ID")
    limit: int = Field(default=100, le=1000, description="Maximum messages to fetch")
    oldest: Optional[str] = Field(None, description="Oldest timestamp (inclusive)")
    latest: Optional[str] = Field(None, description="Latest timestamp (exclusive)")
    include_threads: bool = Field(default=True, description="Include thread replies")

class SlackSearchQuery(BaseModel):
    """Query parameters for searching Slack messages."""

    query: str = Field(..., description="Search query")
    sort: str = Field(default="timestamp", description="Sort field")
    sort_dir: str = Field(default="desc", description="Sort direction")
    count: int = Field(default=20, le=1000, description="Number of results")

class SlackWebhookSetupRequest(BaseModel):
    """Request model for setting up Slack webhooks."""

    event_url: str = Field(..., description="URL to receive event callbacks")

# API Endpoints

@router.post("/setup", response_model=Dict[str, Any])
async def setup_slack_integration(
    request: SlackIntegrationSetupRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Set up Slack integration for the organization.

    This endpoint configures the Slack connector and creates the integration
    configuration for the organization.
    """
    try:
        # Register Slack connector if not already registered
        try:
            connector_id = await slack_integration_service.register_slack_connector()
        except Exception:
            # Connector might already exist
            connector_id = "existing"

        # Install connector for organization
        installation_config = {
            "client_id": request.client_id,
            "client_secret": request.client_secret,
            "signing_secret": request.signing_secret,
            "channels": request.channels,
            "keywords": request.keywords,
            "sync_frequency": request.sync_frequency,
            "include_files": request.include_files,
            "include_reactions": request.include_reactions,
            "thread_depth": request.thread_depth,
        }

        # Create integration record
        from app.models.integration import Integration

        integration = Integration(
            organization_id=current_org.id,
            configured_by_user_id=current_user.id,
            service_type="slack",
            service_name="Slack Workspace",
            integration_key=f"slack-{current_org.id}",
            config=installation_config,
            capabilities=[
                "read_messages",
                "read_channels",
                "read_users",
                "read_files",
                "search_messages",
                "real_time_events",
            ],
            scopes=slack_integration_service.required_scopes,
            status="pending_auth",
        )

        session.add(integration)
        await session.commit()
        await session.refresh(integration)

        logger.info(f"Slack integration setup for organization {current_org.id}")

        return {
            "success": True,
            "integration_id": integration.id,
            "status": "configured",
            "message": "Slack integration configured. Complete OAuth to activate.",
            "next_step": "oauth_authorization",
        }

    except Exception as e:
        logger.error(f"Error setting up Slack integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup Slack integration: {str(e)}",
        )

@router.post("/oauth/initiate", response_model=SlackOAuthInitiateResponse)
async def initiate_slack_oauth(
    request: SlackOAuthInitiateRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> SlackOAuthInitiateResponse:
    """Initiate Slack OAuth 2.0 authorization flow.

    Returns the authorization URL that the user should visit to grant
    permissions to the Slack workspace.
    """
    try:
        authorization_url = await slack_integration_service.initiate_oauth_flow(
            organization_id=current_org.id,
            user_id=current_user.id,
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

        return SlackOAuthInitiateResponse(
            authorization_url=authorization_url, state=state
        )

    except Exception as e:
        logger.error(f"Error initiating Slack OAuth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate OAuth: {str(e)}",
        )

@router.post("/oauth/complete", response_model=SlackOAuthCompleteResponse)
async def complete_slack_oauth(
    request: SlackOAuthCompleteRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> SlackOAuthCompleteResponse:
    """Complete Slack OAuth 2.0 authorization flow.

    Exchanges the authorization code for access tokens and stores them
    securely for the organization.
    """
    try:
        oauth_token = await slack_integration_service.complete_oauth_flow(
            organization_id=current_org.id,
            user_id=current_user.id,
            authorization_code=request.code,
            redirect_uri=request.redirect_uri,
        )

        # Get integration to extract team info
        from sqlalchemy import select

        from app.models.integration import Integration

        integration_query = select(Integration).where(
            Integration.id == oauth_token.integration_id
        )
        result = await session.execute(integration_query)
        integration = result.scalar_one()

        team_name = integration.integration_metadata.get("team_name", "Unknown")
        user_name = oauth_token.external_username or "Unknown"

        return SlackOAuthCompleteResponse(
            success=True,
            token_id=oauth_token.id,
            team_name=team_name,
            user_name=user_name,
        )

    except Exception as e:
        logger.error(f"Error completing Slack OAuth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete OAuth: {str(e)}",
        )

@router.get("/channels", response_model=List[SlackChannelResponse])
async def get_slack_channels(
    include_private: bool = Query(default=True, description="Include private channels"),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> List[SlackChannelResponse]:
    """Get all accessible Slack channels for the organization.

    Returns a list of all channels the integration has access to,
    including public and optionally private channels.
    """
    try:
        # Get the organization's Slack integration
        from sqlalchemy import and_, select

        from app.models.integration import Integration

        integration_query = select(Integration).where(
            and_(
                Integration.organization_id == current_org.id,
                Integration.service_type == "slack",
                Integration.status == "active",
            )
        )
        result = await session.execute(integration_query)
        integration = result.scalar_one_or_none()

        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active Slack integration found",
            )

        # Fetch channels from Slack
        channels = await slack_integration_service.fetch_channels(
            integration_id=integration.id, include_private=include_private
        )

        # Convert to response format
        channel_responses = []
        for channel in channels:
            channel_responses.append(
                SlackChannelResponse(
                    id=channel["id"],
                    name=channel["name"],
                    is_private=channel.get("is_private", False),
                    is_archived=channel.get("is_archived", False),
                    member_count=channel.get("num_members", 0),
                    purpose=channel.get("purpose", {}).get("value"),
                    topic=channel.get("topic", {}).get("value"),
                )
            )

        return channel_responses

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Slack channels: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch channels: {str(e)}",
        )

@router.post("/messages", response_model=List[Dict[str, Any]])
async def get_slack_messages(
    query: SlackMessageQuery,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> List[Dict[str, Any]]:
    """Fetch messages from a specific Slack channel.

    Returns messages from the specified channel with optional filtering
    by time range and thread inclusion.
    """
    try:
        # Get the organization's Slack integration
        from sqlalchemy import and_, select

        from app.models.integration import Integration

        integration_query = select(Integration).where(
            and_(
                Integration.organization_id == current_org.id,
                Integration.service_type == "slack",
                Integration.status == "active",
            )
        )
        result = await session.execute(integration_query)
        integration = result.scalar_one_or_none()

        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active Slack integration found",
            )

        # Fetch messages from Slack
        messages = await slack_integration_service.fetch_messages(
            integration_id=integration.id,
            channel_id=query.channel_id,
            limit=query.limit,
            oldest=query.oldest,
            latest=query.latest,
            include_threads=query.include_threads,
        )

        return messages

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Slack messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch messages: {str(e)}",
        )

@router.post("/search", response_model=Dict[str, Any])
async def search_slack_messages(
    query: SlackSearchQuery,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Search messages across the Slack workspace.

    Searches all accessible channels and direct messages for the
    specified query string.
    """
    try:
        # Get the organization's Slack integration
        from sqlalchemy import and_, select

        from app.models.integration import Integration

        integration_query = select(Integration).where(
            and_(
                Integration.organization_id == current_org.id,
                Integration.service_type == "slack",
                Integration.status == "active",
            )
        )
        result = await session.execute(integration_query)
        integration = result.scalar_one_or_none()

        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active Slack integration found",
            )

        # Search messages in Slack
        search_results = await slack_integration_service.search_messages(
            integration_id=integration.id,
            query=query.query,
            sort=query.sort,
            sort_dir=query.sort_dir,
            count=query.count,
        )

        return search_results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching Slack messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search messages: {str(e)}",
        )

@router.post("/webhooks/setup", response_model=Dict[str, Any])
async def setup_slack_webhooks(
    request: SlackWebhookSetupRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Set up real-time event webhooks for Slack.

    Configures the integration to receive real-time events from Slack
    via the Events API.
    """
    try:
        # Get the organization's Slack integration
        from sqlalchemy import and_, select

        from app.models.integration import Integration

        integration_query = select(Integration).where(
            and_(
                Integration.organization_id == current_org.id,
                Integration.service_type == "slack",
                Integration.status == "active",
            )
        )
        result = await session.execute(integration_query)
        integration = result.scalar_one_or_none()

        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active Slack integration found",
            )

        # Set up real-time events
        event_config = await slack_integration_service.setup_real_time_events(
            integration_id=integration.id, event_url=request.event_url
        )

        return {
            "success": True,
            "webhook_url": event_config["webhook_url"],
            "event_types": event_config["event_types"],
            "message": "Real-time events configured successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up Slack webhooks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup webhooks: {str(e)}",
        )

@router.post("/webhooks/events")
async def handle_slack_webhook_event(
    request: Request, session: AsyncSession = Depends(get_db_session)
) -> JSONResponse:
    """Handle incoming webhook events from Slack.

    This endpoint receives real-time events from Slack via the Events API
    and processes them for data synchronization.
    """
    try:
        # Get request body and headers
        body = await request.body()
        headers = dict(request.headers)

        # Parse JSON body

        event_data = json.loads(body.decode())

        # Handle URL verification challenge
        if event_data.get("type") == "url_verification":
            return JSONResponse(
                content={"challenge": event_data.get("challenge")}, status_code=200
            )

        # Get team ID to find the integration
        team_id = event_data.get("team_id")
        if not team_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No team_id in event data",
            )

        # Find integration by team ID
        from sqlalchemy import select

        from app.models.integration import Integration

        integration_query = select(Integration).where(
            Integration.service_type == "slack"
        )
        result = await session.execute(integration_query)
        integrations = result.scalars().all()

        integration = None
        for integ in integrations:
            if (
                integ.integration_metadata
                and integ.integration_metadata.get("team_id") == team_id
            ):
                integration = integ
                break

        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No integration found for team",
            )

        # Process the event
        success = await slack_integration_service.process_webhook_event(
            integration_id=integration.id, event_data=event_data, headers=headers
        )

        if success:
            return JSONResponse(content={"status": "ok"}, status_code=200)
        else:
            return JSONResponse(
                content={"error": "Event processing failed"}, status_code=500
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling Slack webhook event: {e}")
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.get("/status", response_model=Dict[str, Any])
async def get_slack_integration_status(
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Get the status of the Slack integration for the organization.

    Returns information about the integration status, connected workspace,
    and configuration details.
    """
    try:
        # Get the organization's Slack integration
        from sqlalchemy import and_, select

        from app.models.integration import Integration

        integration_query = select(Integration).where(
            and_(
                Integration.organization_id == current_org.id,
                Integration.service_type == "slack",
            )
        )
        result = await session.execute(integration_query)
        integration = result.scalar_one_or_none()

        if not integration:
            return {
                "configured": False,
                "status": "not_configured",
                "message": "Slack integration not configured",
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

        # Get data sources (channels)
        from app.models.integration import DataSource

        sources_query = select(DataSource).where(
            DataSource.integration_id == integration.id
        )
        sources_result = await session.execute(sources_query)
        data_sources = sources_result.scalars().all()

        return {
            "configured": True,
            "status": integration.status,
            "health_status": integration.health_status,
            "team_name": (
                integration.integration_metadata.get("team_name")
                if integration.integration_metadata
                else None
            ),
            "connected_user": oauth_token.external_username if oauth_token else None,
            "channels_synced": len(
                [ds for ds in data_sources if ds.source_type == "channel"]
            ),
            "real_time_enabled": (
                integration.integration_metadata.get("real_time_enabled", False)
                if integration.integration_metadata
                else False
            ),
            "last_sync": (
                integration.last_sync_at.isoformat()
                if integration.last_sync_at
                else None
            ),
            "webhook_configured": bool(integration.webhook_url),
        }

    except Exception as e:
        logger.error(f"Error getting Slack integration status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get integration status: {str(e)}",
        )
