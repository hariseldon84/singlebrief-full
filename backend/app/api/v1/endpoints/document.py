"""Document Integration API endpoints for SingleBrief.

This module provides REST API endpoints for Google Drive and OneDrive
document integration, OAuth flows, file retrieval, and content extraction.
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
from app.integrations.document_integration import document_service
from app.models.user import Organization, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/document", tags=["document"])

# Pydantic models for request/response

class DocumentSetupRequest(BaseModel):
    """Request model for setting up document integration."""

    service_type: str = Field(..., description="Service type: gdrive or onedrive")
    client_id: str = Field(..., description="OAuth client ID")
    client_secret: str = Field(..., description="OAuth client secret")
    tenant_id: Optional[str] = Field(
        None, description="Microsoft tenant ID (OneDrive only)"
    )
    sync_frequency: str = Field(default="hourly", description="Sync frequency")
    max_files: int = Field(default=1000, description="Maximum files per batch")
    extract_content: bool = Field(default=True, description="Extract file content")
    include_shared: bool = Field(default=True, description="Include shared files")
    file_types: List[str] = Field(
        default=["docs", "pdf", "txt"], description="File types to process"
    )

class DocumentOAuthInitiateRequest(BaseModel):
    """Request model for initiating OAuth flow."""

    service_type: str = Field(..., description="Service type: gdrive or onedrive")
    redirect_uri: str = Field(..., description="OAuth redirect URI")
    state: Optional[str] = Field(None, description="CSRF protection state")

class DocumentOAuthInitiateResponse(BaseModel):
    """Response model for OAuth initiation."""

    authorization_url: str = Field(..., description="URL for user authorization")
    state: str = Field(..., description="State parameter for verification")
    service_type: str = Field(..., description="Service type")

class DocumentOAuthCompleteRequest(BaseModel):
    """Request model for completing OAuth flow."""

    service_type: str = Field(..., description="Service type: gdrive or onedrive")
    code: str = Field(..., description="Authorization code")
    redirect_uri: str = Field(..., description="OAuth redirect URI")

class DocumentOAuthCompleteResponse(BaseModel):
    """Response model for OAuth completion."""

    success: bool = Field(..., description="Whether OAuth was successful")
    token_id: str = Field(..., description="Created OAuth token ID")
    service_type: str = Field(..., description="Service type")
    user_email: str = Field(..., description="Connected user email")

class DocumentQuery(BaseModel):
    """Query parameters for fetching documents."""

    service_type: str = Field(..., description="Service type: gdrive or onedrive")
    query: Optional[str] = Field(None, description="Search query")
    folder_id: Optional[str] = Field(None, description="Specific folder ID")
    max_results: int = Field(default=100, le=1000, description="Maximum files")
    include_content: bool = Field(default=False, description="Include file content")
    file_types: Optional[List[str]] = Field(None, description="Filter by file types")

class DocumentContentRequest(BaseModel):
    """Request model for extracting document content."""

    service_type: str = Field(..., description="Service type: gdrive or onedrive")
    file_id: str = Field(..., description="File ID to extract content from")

class DocumentRelevanceRequest(BaseModel):
    """Request model for scoring document relevance."""

    service_type: str = Field(..., description="Service type: gdrive or onedrive")
    file_ids: List[str] = Field(..., description="List of file IDs to score")
    context: str = Field(..., description="Context for relevance scoring")

# API Endpoints

@router.post("/setup", response_model=Dict[str, Any])
async def setup_document_integration(
    request: DocumentSetupRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Set up document integration for the organization.

    This endpoint configures the document connector and creates the
    integration configuration for the organization.
    """
    try:
        # Validate service type
        if request.service_type not in ["gdrive", "onedrive"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service type must be 'gdrive' or 'onedrive'",
            )

        # Register connector if not already registered
        try:
            connector_id = await document_service.register_document_connector(
                request.service_type
            )
        except Exception:
            # Connector might already exist
            connector_id = "existing"

        # Create integration configuration
        installation_config = {
            "client_id": request.client_id,
            "client_secret": request.client_secret,
            "sync_frequency": request.sync_frequency,
            "max_files": request.max_files,
            "extract_content": request.extract_content,
            "include_shared": request.include_shared,
            "file_types": request.file_types,
        }

        if request.service_type == "onedrive" and request.tenant_id:
            installation_config["tenant_id"] = request.tenant_id

        # Create integration record
        from app.models.integration import Integration

        integration = Integration(
            organization_id=current_org.id,
            configured_by_user_id=current_user.id,
            service_type=request.service_type,
            service_name=f"{'Google Drive' if request.service_type == 'gdrive' else 'OneDrive'} Documents",
            integration_key=f"{request.service_type}-{current_org.id}",
            config=installation_config,
            capabilities=[
                "read_files",
                "search_files",
                "extract_content",
                "track_changes",
                "relevance_scoring",
                "file_watching",
            ],
            scopes=(
                document_service.gdrive_scopes
                if request.service_type == "gdrive"
                else document_service.onedrive_scopes
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
            "message": f"{'Google Drive' if request.service_type == 'gdrive' else 'OneDrive'} integration configured. Complete OAuth to activate.",
            "next_step": "oauth_authorization",
        }

    except Exception as e:
        logger.error(f"Error setting up {request.service_type} integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup {request.service_type} integration: {str(e)}",
        )

@router.post("/oauth/initiate", response_model=DocumentOAuthInitiateResponse)
async def initiate_document_oauth(
    request: DocumentOAuthInitiateRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> DocumentOAuthInitiateResponse:
    """Initiate OAuth 2.0 authorization flow for document access.

    Returns the authorization URL that the user should visit to grant
    permissions to their documents.
    """
    try:
        authorization_url = await document_service.initiate_oauth_flow(
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

        return DocumentOAuthInitiateResponse(
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

@router.post("/oauth/complete", response_model=DocumentOAuthCompleteResponse)
async def complete_document_oauth(
    request: DocumentOAuthCompleteRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> DocumentOAuthCompleteResponse:
    """Complete OAuth 2.0 authorization flow for document access.

    Exchanges the authorization code for access tokens and stores them
    securely for the organization.
    """
    try:
        oauth_token = await document_service.complete_oauth_flow(
            organization_id=current_org.id,
            user_id=current_user.id,
            service_type=request.service_type,
            authorization_code=request.code,
            redirect_uri=request.redirect_uri,
        )

        return DocumentOAuthCompleteResponse(
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

@router.post("/files", response_model=List[Dict[str, Any]])
async def fetch_documents(
    query: DocumentQuery,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> List[Dict[str, Any]]:
    """Fetch documents from Google Drive or OneDrive.

    Returns files from the specified service with optional search filtering
    and content extraction.
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

        # Fetch files from service
        files = await document_service.fetch_files(
            integration_id=integration.id,
            service_type=query.service_type,
            query=query.query,
            folder_id=query.folder_id,
            max_results=query.max_results,
            include_content=query.include_content,
            file_types=query.file_types,
        )

        return files

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch documents: {str(e)}",
        )

@router.post("/content/extract", response_model=Dict[str, Any])
async def extract_document_content(
    request: DocumentContentRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Extract content from a specific document.

    Returns the extracted text content, metadata, and analysis from
    the specified document.
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

        # Extract file content
        content = await document_service.extract_file_content(
            integration_id=integration.id,
            service_type=request.service_type,
            file_id=request.file_id,
        )

        return content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting document content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract content: {str(e)}",
        )

@router.post("/relevance/score", response_model=List[Dict[str, Any]])
async def score_document_relevance(
    request: DocumentRelevanceRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> List[Dict[str, Any]]:
    """Score document relevance based on context.

    Analyzes documents against the provided context and returns
    relevance scores and explanations.
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

        # Score document relevance
        relevance_scores = await document_service.score_document_relevance(
            integration_id=integration.id,
            service_type=request.service_type,
            file_ids=request.file_ids,
            context=request.context,
        )

        return relevance_scores

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scoring document relevance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to score relevance: {str(e)}",
        )

@router.post("/changes/setup", response_model=Dict[str, Any])
async def setup_change_tracking(
    service_type: str = Query(..., description="Service type: gdrive or onedrive"),
    webhook_url: str = Query(..., description="Webhook URL for change notifications"),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Set up real-time change tracking for documents.

    Configures webhook notifications for file changes, additions,
    and deletions in the connected document service.
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

        # Setup change tracking
        change_config = await document_service.setup_change_tracking(
            integration_id=integration.id,
            service_type=service_type,
            webhook_url=webhook_url,
        )

        return change_config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up change tracking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup change tracking: {str(e)}",
        )

@router.post("/webhooks/changes", response_model=Dict[str, Any])
async def process_change_webhook(
    request: Request,
    service_type: str = Query(..., description="Service type: gdrive or onedrive"),
) -> Dict[str, Any]:
    """Process document change webhook notifications.

    Handles incoming webhook notifications about file changes,
    additions, and deletions from the document service.
    """
    try:
        # Get request data
        if request.headers.get("content-type") == "application/json":
            event_data = await request.json()
        else:
            # Handle other content types (e.g., Google Drive sends various formats)
            event_data = {"raw_body": await request.body()}

        headers = dict(request.headers)

        # Process the webhook event
        result = await document_service.process_change_webhook(
            service_type=service_type, event_data=event_data, headers=headers
        )

        return result

    except Exception as e:
        logger.error(f"Error processing document change webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}",
        )

@router.get("/status", response_model=Dict[str, Any])
async def get_document_integration_status(
    service_type: str = Query(..., description="Service type: gdrive or onedrive"),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Get the status of document integration for the organization.

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
                "message": f"{'Google Drive' if service_type == 'gdrive' else 'OneDrive'} integration not configured",
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

        document_sources = [ds for ds in data_sources if ds.source_type == "document"]
        folder_sources = [ds for ds in data_sources if ds.source_type == "folder"]

        return {
            "configured": True,
            "status": integration.status,
            "health_status": integration.health_status,
            "service_type": service_type,
            "connected_email": oauth_token.external_email if oauth_token else None,
            "connected_user": oauth_token.external_username if oauth_token else None,
            "document_sources": len(document_sources),
            "folder_sources": len(folder_sources),
            "last_sync": (
                integration.last_sync_at.isoformat()
                if integration.last_sync_at
                else None
            ),
            "sync_frequency": integration.config.get("sync_frequency", "hourly"),
            "max_files": integration.config.get("max_files", 1000),
            "extract_content": integration.config.get("extract_content", True),
            "include_shared": integration.config.get("include_shared", True),
            "file_types": integration.config.get("file_types", ["docs", "pdf", "txt"]),
        }

    except Exception as e:
        logger.error(f"Error getting {service_type} integration status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get integration status: {str(e)}",
        )
