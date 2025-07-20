"""Developer Tools Integration API endpoints for SingleBrief.

This module provides REST API endpoints for GitHub and Jira integration,
OAuth flows, repository/project tracking, and development metrics.
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
from app.integrations.developer_tools_integration import \
    developer_tools_service
from app.models.user import Organization, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/developer-tools", tags=["developer-tools"])

# Pydantic models for request/response

class DeveloperToolsSetupRequest(BaseModel):
    """Request model for setting up developer tools integration."""

    service_type: str = Field(..., description="Service type: github or jira")
    client_id: str = Field(..., description="OAuth client ID")
    client_secret: str = Field(..., description="OAuth client secret")
    organization: Optional[str] = Field(
        None, description="GitHub organization or Jira site"
    )
    repositories: List[str] = Field(
        default=[], description="GitHub repositories to track"
    )
    projects: List[str] = Field(default=[], description="Jira projects to track")
    sync_frequency: str = Field(default="hourly", description="Sync frequency")
    track_metrics: bool = Field(default=True, description="Track development metrics")
    include_webhooks: bool = Field(
        default=False, description="Setup webhook notifications"
    )

class DeveloperToolsOAuthInitiateRequest(BaseModel):
    """Request model for initiating OAuth flow."""

    service_type: str = Field(..., description="Service type: github or jira")
    redirect_uri: str = Field(..., description="OAuth redirect URI")
    state: Optional[str] = Field(None, description="CSRF protection state")

class DeveloperToolsOAuthInitiateResponse(BaseModel):
    """Response model for OAuth initiation."""

    authorization_url: str = Field(..., description="URL for user authorization")
    state: str = Field(..., description="State parameter for verification")
    service_type: str = Field(..., description="Service type")

class DeveloperToolsOAuthCompleteRequest(BaseModel):
    """Request model for completing OAuth flow."""

    service_type: str = Field(..., description="Service type: github or jira")
    code: str = Field(..., description="Authorization code")
    redirect_uri: str = Field(..., description="OAuth redirect URI")

class DeveloperToolsOAuthCompleteResponse(BaseModel):
    """Response model for OAuth completion."""

    success: bool = Field(..., description="Whether OAuth was successful")
    token_id: str = Field(..., description="Created OAuth token ID")
    service_type: str = Field(..., description="Service type")
    username: str = Field(..., description="Connected username")

class RepositoryQuery(BaseModel):
    """Query parameters for fetching repositories."""

    include_private: bool = Field(
        default=True, description="Include private repositories"
    )
    language: Optional[str] = Field(None, description="Filter by programming language")
    sort: str = Field(
        default="updated", description="Sort order: updated, created, pushed, full_name"
    )

class PullRequestQuery(BaseModel):
    """Query parameters for fetching pull requests."""

    repository: str = Field(..., description="Repository name (owner/repo)")
    state: str = Field(default="all", description="PR state: open, closed, all")
    limit: int = Field(default=100, le=100, description="Maximum PRs to fetch")
    include_reviews: bool = Field(
        default=True, description="Include review information"
    )

class JiraIssueQuery(BaseModel):
    """Query parameters for fetching Jira issues."""

    project_key: str = Field(..., description="Jira project key")
    jql: Optional[str] = Field(None, description="Custom JQL query")
    limit: int = Field(default=100, le=100, description="Maximum issues to fetch")
    include_details: bool = Field(
        default=True, description="Include detailed issue information"
    )

class MetricsQuery(BaseModel):
    """Query parameters for development metrics."""

    service_type: str = Field(..., description="Service type: github or jira")
    time_period_days: int = Field(default=30, le=365, description="Time period in days")
    include_velocity: bool = Field(default=True, description="Include velocity metrics")
    include_contributors: bool = Field(
        default=True, description="Include contributor stats"
    )

class WebhookSetupRequest(BaseModel):
    """Request model for setting up webhooks."""

    service_type: str = Field(..., description="Service type: github or jira")
    webhook_url: str = Field(..., description="Webhook endpoint URL")
    events: List[str] = Field(default=[], description="Events to subscribe to")
    secret: Optional[str] = Field(None, description="Webhook secret for verification")

# API Endpoints

@router.post("/setup", response_model=Dict[str, Any])
async def setup_developer_tools_integration(
    request: DeveloperToolsSetupRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Set up developer tools integration for the organization.

    This endpoint configures the GitHub or Jira connector and creates the
    integration configuration for the organization.
    """
    try:
        # Validate service type
        if request.service_type not in ["github", "jira"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service type must be 'github' or 'jira'",
            )

        # Register connector if not already registered
        try:
            connector_id = (
                await developer_tools_service.register_developer_tools_connector(
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
            "organization": request.organization,
            "repositories": request.repositories,
            "projects": request.projects,
            "sync_frequency": request.sync_frequency,
            "track_metrics": request.track_metrics,
            "include_webhooks": request.include_webhooks,
        }

        # Create integration record
        from app.models.integration import Integration

        service_name = "GitHub" if request.service_type == "github" else "Jira"

        integration = Integration(
            organization_id=current_org.id,
            configured_by_user_id=current_user.id,
            service_type=request.service_type,
            service_name=f"{service_name} Development Tools",
            integration_key=f"{request.service_type}-{current_org.id}",
            config=installation_config,
            capabilities=[
                (
                    "read_repositories"
                    if request.service_type == "github"
                    else "read_projects"
                ),
                "read_issues",
                (
                    "read_pull_requests"
                    if request.service_type == "github"
                    else "read_tickets"
                ),
                "track_metrics",
                "webhook_events",
                "development_analytics",
            ],
            scopes=(
                developer_tools_service.github_scopes
                if request.service_type == "github"
                else developer_tools_service.jira_scopes
            ),
            status="pending_auth",
        )

        session.add(integration)
        await session.commit()
        await session.refresh(integration)

        logger.info(
            f"{service_name} integration setup for organization {current_org.id}"
        )

        return {
            "success": True,
            "integration_id": integration.id,
            "service_type": request.service_type,
            "status": "configured",
            "message": f"{service_name} integration configured. Complete OAuth to activate.",
            "next_step": "oauth_authorization",
        }

    except Exception as e:
        logger.error(f"Error setting up {request.service_type} integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup {request.service_type} integration: {str(e)}",
        )

@router.post("/oauth/initiate", response_model=DeveloperToolsOAuthInitiateResponse)
async def initiate_developer_tools_oauth(
    request: DeveloperToolsOAuthInitiateRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> DeveloperToolsOAuthInitiateResponse:
    """Initiate OAuth 2.0 authorization flow for developer tools access.

    Returns the authorization URL that the user should visit to grant
    permissions to their GitHub or Jira account.
    """
    try:
        authorization_url = await developer_tools_service.initiate_oauth_flow(
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

        return DeveloperToolsOAuthInitiateResponse(
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

@router.post("/oauth/complete", response_model=DeveloperToolsOAuthCompleteResponse)
async def complete_developer_tools_oauth(
    request: DeveloperToolsOAuthCompleteRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> DeveloperToolsOAuthCompleteResponse:
    """Complete OAuth 2.0 authorization flow for developer tools access.

    Exchanges the authorization code for access tokens and stores them
    securely for the organization.
    """
    try:
        oauth_token = await developer_tools_service.complete_oauth_flow(
            organization_id=current_org.id,
            user_id=current_user.id,
            service_type=request.service_type,
            authorization_code=request.code,
            redirect_uri=request.redirect_uri,
        )

        return DeveloperToolsOAuthCompleteResponse(
            success=True,
            token_id=oauth_token.id,
            service_type=request.service_type,
            username=oauth_token.external_username or "Unknown",
        )

    except Exception as e:
        logger.error(f"Error completing {request.service_type} OAuth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete OAuth: {str(e)}",
        )

@router.post("/github/repositories", response_model=List[Dict[str, Any]])
async def fetch_github_repositories(
    query: RepositoryQuery,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> List[Dict[str, Any]]:
    """Fetch GitHub repositories for the authenticated user/organization.

    Returns repositories with metadata including language, stars, forks,
    and recent activity information.
    """
    try:
        # Get the organization's GitHub integration
        from sqlalchemy import and_, select

        from app.models.integration import Integration

        integration_query = select(Integration).where(
            and_(
                Integration.organization_id == current_org.id,
                Integration.service_type == "github",
                Integration.status == "active",
            )
        )
        result = await session.execute(integration_query)
        integration = result.scalar_one_or_none()

        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active GitHub integration found",
            )

        # Fetch repositories
        repositories = await developer_tools_service.fetch_repositories(integration.id)

        # Apply filters
        filtered_repos = repositories

        if not query.include_private:
            filtered_repos = [r for r in filtered_repos if not r.get("private", False)]

        if query.language:
            filtered_repos = [
                r for r in filtered_repos if r.get("language") == query.language
            ]

        # Sort repositories
        if query.sort == "updated":
            filtered_repos.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        elif query.sort == "created":
            filtered_repos.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        elif query.sort == "pushed":
            filtered_repos.sort(key=lambda x: x.get("pushed_at", ""), reverse=True)
        elif query.sort == "full_name":
            filtered_repos.sort(key=lambda x: x.get("full_name", ""))

        return filtered_repos

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching GitHub repositories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch repositories: {str(e)}",
        )

@router.post("/github/pull-requests", response_model=List[Dict[str, Any]])
async def fetch_github_pull_requests(
    query: PullRequestQuery,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> List[Dict[str, Any]]:
    """Fetch GitHub pull requests for a specific repository.

    Returns pull requests with review status, approval information,
    and merge statistics.
    """
    try:
        # Get the organization's GitHub integration
        from sqlalchemy import and_, select

        from app.models.integration import Integration

        integration_query = select(Integration).where(
            and_(
                Integration.organization_id == current_org.id,
                Integration.service_type == "github",
                Integration.status == "active",
            )
        )
        result = await session.execute(integration_query)
        integration = result.scalar_one_or_none()

        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active GitHub integration found",
            )

        # Fetch pull requests
        pull_requests = await developer_tools_service.fetch_pull_requests(
            integration_id=integration.id,
            repository=query.repository,
            state=query.state,
            limit=query.limit,
        )

        return pull_requests

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching GitHub pull requests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch pull requests: {str(e)}",
        )

@router.post("/jira/issues", response_model=List[Dict[str, Any]])
async def fetch_jira_issues(
    query: JiraIssueQuery,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> List[Dict[str, Any]]:
    """Fetch Jira issues for a specific project.

    Returns issues with status, priority, assignee, and progress information.
    """
    try:
        # Get the organization's Jira integration
        from sqlalchemy import and_, select

        from app.models.integration import Integration

        integration_query = select(Integration).where(
            and_(
                Integration.organization_id == current_org.id,
                Integration.service_type == "jira",
                Integration.status == "active",
            )
        )
        result = await session.execute(integration_query)
        integration = result.scalar_one_or_none()

        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active Jira integration found",
            )

        # Fetch Jira issues
        issues = await developer_tools_service.fetch_jira_issues(
            integration_id=integration.id,
            project_key=query.project_key,
            jql=query.jql,
            limit=query.limit,
        )

        return issues

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Jira issues: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch issues: {str(e)}",
        )

@router.post("/metrics/analyze", response_model=Dict[str, Any])
async def analyze_development_metrics(
    query: MetricsQuery,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Analyze development metrics for the specified time period.

    Returns comprehensive metrics including velocity, contributor statistics,
    issue resolution times, and team performance indicators.
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

        # Analyze metrics
        metrics = await developer_tools_service.analyze_development_metrics(
            integration_id=integration.id,
            service_type=query.service_type,
            time_period_days=query.time_period_days,
        )

        # Add metadata
        metrics["analysis_period"] = {
            "days": query.time_period_days,
            "start_date": (
                datetime.now(timezone.utc) - timedelta(days=query.time_period_days)
            ).isoformat(),
            "end_date": datetime.now(timezone.utc).isoformat(),
        }
        metrics["service_type"] = query.service_type
        metrics["organization_id"] = current_org.id

        return metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing development metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze metrics: {str(e)}",
        )

@router.post("/webhooks/setup", response_model=Dict[str, Any])
async def setup_developer_tools_webhooks(
    request: WebhookSetupRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Set up webhooks for real-time development notifications.

    Configures webhook endpoints for receiving real-time updates about
    repository changes, pull requests, issues, and other development events.
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

        # Setup webhooks
        webhook_config = await developer_tools_service.setup_webhooks(
            integration_id=integration.id,
            service_type=request.service_type,
            webhook_url=request.webhook_url,
        )

        return webhook_config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up webhooks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup webhooks: {str(e)}",
        )

@router.post("/webhooks/events", response_model=Dict[str, Any])
async def process_developer_tools_webhook(
    request: Request,
    service_type: str = Query(..., description="Service type: github or jira"),
) -> Dict[str, Any]:
    """Process incoming webhook events from developer tools.

    Handles webhook notifications for repository changes, pull requests,
    issues, commits, and other development events.
    """
    try:
        # Get request data
        if request.headers.get("content-type", "").startswith("application/json"):
            event_data = await request.json()
        else:
            # Handle other content types
            event_data = {"raw_body": await request.body()}

        headers = dict(request.headers)

        # Extract integration ID from headers or path (implementation specific)
        integration_id = headers.get("x-integration-id", "default")

        # Process the webhook event
        success = await developer_tools_service.process_webhook_event(
            integration_id=integration_id,
            service_type=service_type,
            event_data=event_data,
            headers=headers,
        )

        return {"success": success, "processed": True}

    except Exception as e:
        logger.error(f"Error processing developer tools webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}",
        )

@router.get("/status", response_model=Dict[str, Any])
async def get_developer_tools_integration_status(
    service_type: str = Query(..., description="Service type: github or jira"),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Get the status of developer tools integration for the organization.

    Returns information about the integration status, connected account,
    tracked repositories/projects, and configuration details.
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
            service_name = "GitHub" if service_type == "github" else "Jira"
            return {
                "configured": False,
                "status": "not_configured",
                "service_type": service_type,
                "message": f"{service_name} integration not configured",
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

        if service_type == "github":
            repository_sources = [
                ds for ds in data_sources if ds.source_type == "repository"
            ]
            tracked_items = len(repository_sources)
            tracked_type = "repositories"
        else:  # jira
            project_sources = [ds for ds in data_sources if ds.source_type == "project"]
            tracked_items = len(project_sources)
            tracked_type = "projects"

        return {
            "configured": True,
            "status": integration.status,
            "health_status": integration.health_status,
            "service_type": service_type,
            "connected_username": (
                oauth_token.external_username if oauth_token else None
            ),
            "connected_email": oauth_token.external_email if oauth_token else None,
            "tracked_items": tracked_items,
            "tracked_type": tracked_type,
            "last_sync": (
                integration.last_sync_at.isoformat()
                if integration.last_sync_at
                else None
            ),
            "sync_frequency": integration.config.get("sync_frequency", "hourly"),
            "track_metrics": integration.config.get("track_metrics", True),
            "webhooks_enabled": integration.config.get("include_webhooks", False),
            "organization": integration.config.get("organization"),
            "repositories": integration.config.get("repositories", []),
            "projects": integration.config.get("projects", []),
        }

    except Exception as e:
        logger.error(f"Error getting {service_type} integration status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get integration status: {str(e)}",
        )
