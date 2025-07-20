"""Document and File System Integration Service for SingleBrief.

This module implements Google Drive and OneDrive integration for document access,
content extraction, version tracking, and real-time change notifications.
"""

from typing import Any, Dict, List, Optional, Tuple

import base64
import hashlib
import io
import logging
import mimetypes
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlencode

import aiohttp
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.integration_hub import IntegrationHubService
from app.core.config import settings
from app.core.database import get_db_session
from app.models.integration import (DataSource, Integration, IntegrationLog,
                                    OAuthToken)
from app.models.user import Organization, User

logger = logging.getLogger(__name__)

class DocumentIntegrationService:
    """Service for Google Drive and OneDrive document integration."""

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
        self.integration_hub = IntegrationHubService(session)

        # Google Drive API configuration
        self.drive_base_url = "https://www.googleapis.com/drive/v3"
        self.drive_upload_url = "https://www.googleapis.com/upload/drive/v3"
        self.drive_oauth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.drive_token_url = "https://oauth2.googleapis.com/token"

        # OneDrive API configuration
        self.onedrive_base_url = "https://graph.microsoft.com/v1.0"
        self.onedrive_oauth_url = (
            "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
        )
        self.onedrive_token_url = (
            "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        )

        # Google Drive scopes
        self.drive_scopes = [
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/drive.metadata.readonly",
            "https://www.googleapis.com/auth/drive.file",
        ]

        # OneDrive scopes
        self.onedrive_scopes = [
            "https://graph.microsoft.com/files.read",
            "https://graph.microsoft.com/files.read.all",
            "https://graph.microsoft.com/user.read",
        ]

        # Supported file types for content extraction
        self.supported_file_types = {
            # Text documents
            "application/pdf": "pdf",
            "application/msword": "doc",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
            "text/plain": "txt",
            "text/markdown": "md",
            "text/html": "html",
            # Spreadsheets
            "application/vnd.ms-excel": "xls",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
            "text/csv": "csv",
            # Presentations
            "application/vnd.ms-powerpoint": "ppt",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
            # Google Workspace
            "application/vnd.google-apps.document": "gdoc",
            "application/vnd.google-apps.spreadsheet": "gsheet",
            "application/vnd.google-apps.presentation": "gslides",
            # Images
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/gif": "gif",
            "image/svg+xml": "svg",
        }

        # Rate limits
        self.rate_limits = {
            "drive": 1000,  # 1000 requests per 100 seconds
            "onedrive": 10000,  # 10000 requests per 10 minutes
        }

    async def register_document_connector(self, service_type: str) -> str:
        """Register document connector in Integration Hub.

        Args:
            service_type: Either 'drive' or 'onedrive'

        Returns:
            Connector ID
        """
        try:
            if service_type == "drive":
                config_schema = {
                    "type": "object",
                    "properties": {
                        "client_id": {
                            "type": "string",
                            "description": "Google OAuth client ID",
                        },
                        "client_secret": {
                            "type": "string",
                            "description": "Google OAuth client secret",
                        },
                        "sync_frequency": {
                            "type": "string",
                            "enum": ["realtime", "hourly", "daily"],
                            "default": "hourly",
                        },
                        "max_files": {
                            "type": "integer",
                            "default": 10000,
                            "description": "Maximum files to sync per batch",
                        },
                        "extract_content": {
                            "type": "boolean",
                            "default": true,
                            "description": "Whether to extract file content for indexing",
                        },
                        "supported_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "default": ["pdf", "docx", "txt", "gdoc"],
                            "description": "File types to process",
                        },
                        "folders": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific folder IDs to monitor (empty for all)",
                        },
                        "exclude_folders": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Folder IDs to exclude from sync",
                        },
                    },
                    "required": ["client_id", "client_secret"],
                }

                name = "Google Drive Integration"
                scopes = self.drive_scopes

            else:  # onedrive
                config_schema = {
                    "type": "object",
                    "properties": {
                        "client_id": {
                            "type": "string",
                            "description": "Microsoft app client ID",
                        },
                        "client_secret": {
                            "type": "string",
                            "description": "Microsoft app client secret",
                        },
                        "tenant_id": {
                            "type": "string",
                            "description": "Microsoft tenant ID (optional)",
                        },
                        "sync_frequency": {
                            "type": "string",
                            "enum": ["realtime", "hourly", "daily"],
                            "default": "hourly",
                        },
                        "max_files": {
                            "type": "integer",
                            "default": 10000,
                            "description": "Maximum files to sync per batch",
                        },
                        "extract_content": {
                            "type": "boolean",
                            "default": true,
                            "description": "Whether to extract file content for indexing",
                        },
                        "supported_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "default": ["pdf", "docx", "txt", "xlsx"],
                            "description": "File types to process",
                        },
                        "folders": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific folder paths to monitor (empty for all)",
                        },
                    },
                    "required": ["client_id", "client_secret"],
                }

                name = "OneDrive Integration"
                scopes = self.onedrive_scopes

            connector = await self.integration_hub.register_connector(
                connector_type=service_type,
                name=name,
                version="1.0.0",
                developer="SingleBrief",
                capabilities=[
                    "read_files",
                    "content_extraction",
                    "version_tracking",
                    "change_notifications",
                    "document_search",
                    "permission_control",
                    "relevance_scoring",
                ],
                config_schema=config_schema,
                description=f"Integration for {service_type.title()} document storage",
                required_scopes=scopes,
                supported_auth_types=["oauth2"],
                default_rate_limit_hour=self.rate_limits.get(service_type, 1000),
                default_rate_limit_day=self.rate_limits.get(service_type, 1000) * 24,
                burst_limit=100,
                is_official=True,
                is_verified=True,
            )

            logger.info(f"Registered {service_type} connector: {connector.id}")
            return connector.id

        except Exception as e:
            logger.error(f"Error registering {service_type} connector: {e}")
            raise

    async def initiate_oauth_flow(
        self,
        organization_id: str,
        user_id: str,
        service_type: str,
        redirect_uri: str,
        state: Optional[str] = None,
    ) -> str:
        """Initiate OAuth 2.0 flow for document access.

        Args:
            organization_id: Organization ID
            user_id: User ID
            service_type: 'drive' or 'onedrive'
            redirect_uri: OAuth redirect URI
            state: CSRF protection state

        Returns:
            Authorization URL
        """
        try:
            session = self.session or await get_db_session().__anext__()

            # Get integration configuration
            integration_query = select(Integration).where(
                and_(
                    Integration.organization_id == organization_id,
                    Integration.service_type == service_type,
                )
            )
            result = await session.execute(integration_query)
            integration = result.scalar_one_or_none()

            if not integration:
                raise ValueError(f"{service_type} integration not configured")

            client_id = integration.config.get("client_id")
            if not client_id:
                raise ValueError(f"{service_type} client_id not configured")

            # Generate state if not provided
            if not state:
                state = hashlib.sha256(
                    f"{organization_id}:{user_id}:{datetime.now().isoformat()}".encode()
                ).hexdigest()

            # Build authorization URL
            if service_type == "drive":
                auth_params = {
                    "client_id": client_id,
                    "response_type": "code",
                    "scope": " ".join(self.drive_scopes),
                    "redirect_uri": redirect_uri,
                    "state": state,
                    "access_type": "offline",
                    "prompt": "consent",
                }
                auth_url = f"{self.drive_oauth_url}?{urlencode(auth_params)}"

            else:  # onedrive
                auth_params = {
                    "client_id": client_id,
                    "response_type": "code",
                    "scope": " ".join(self.onedrive_scopes),
                    "redirect_uri": redirect_uri,
                    "state": state,
                    "response_mode": "query",
                }
                auth_url = f"{self.onedrive_oauth_url}?{urlencode(auth_params)}"

            # Log OAuth initiation
            await self._log_operation(
                integration.id,
                user_id,
                "oauth_initiate",
                f"OAuth flow initiated for {service_type}",
                {"service_type": service_type, "redirect_uri": redirect_uri},
            )

            return auth_url

        except Exception as e:
            logger.error(f"Error initiating OAuth flow: {e}")
            raise
        finally:
            if not self.session:
                await session.close()

    async def complete_oauth_flow(
        self,
        organization_id: str,
        user_id: str,
        service_type: str,
        authorization_code: str,
        redirect_uri: str,
    ) -> OAuthToken:
        """Complete OAuth flow and store tokens.

        Args:
            organization_id: Organization ID
            user_id: User ID
            service_type: 'drive' or 'onedrive'
            authorization_code: Auth code from provider
            redirect_uri: OAuth redirect URI

        Returns:
            Created OAuthToken
        """
        session = self.session or await get_db_session().__anext__()

        try:
            # Get integration
            integration_query = select(Integration).where(
                and_(
                    Integration.organization_id == organization_id,
                    Integration.service_type == service_type,
                )
            )
            result = await session.execute(integration_query)
            integration = result.scalar_one_or_none()

            if not integration:
                raise ValueError(f"{service_type} integration not found")

            client_id = integration.config.get("client_id")
            client_secret = integration.config.get("client_secret")

            if not client_id or not client_secret:
                raise ValueError(f"{service_type} client credentials not configured")

            # Exchange code for tokens
            if service_type == "drive":
                token_url = self.drive_token_url
                token_data = {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": authorization_code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                }
            else:  # onedrive
                token_url = self.onedrive_token_url
                token_data = {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": authorization_code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                }

            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(token_url, data=token_data) as response:
                    response_data = await response.json()

                    if response.status != 200:
                        error = response_data.get("error", "Unknown error")
                        raise ValueError(f"Token exchange failed: {error}")

            # Extract token information
            access_token = response_data["access_token"]
            refresh_token = response_data.get("refresh_token")
            expires_in = response_data.get("expires_in", 3600)
            scope = response_data.get("scope", "")

            # Get user profile information
            profile_info = await self._get_user_profile(access_token, service_type)

            # Encrypt and store tokens
            encrypted_access_token = self._encrypt_token(access_token)
            encrypted_refresh_token = (
                self._encrypt_token(refresh_token) if refresh_token else None
            )

            oauth_token = OAuthToken(
                integration_id=integration.id,
                user_id=user_id,
                access_token_encrypted=encrypted_access_token,
                refresh_token_encrypted=encrypted_refresh_token,
                token_type="Bearer",
                scopes=scope.split(" ") if scope else [],
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
                external_user_id=profile_info.get("id"),
                external_username=profile_info.get("username"),
                external_email=profile_info.get("email"),
                encryption_key_id="default",
                encryption_algorithm="AES-256-GCM",
            )

            session.add(oauth_token)

            # Update integration metadata
            integration.integration_metadata = {
                **(integration.integration_metadata or {}),
                "user_profile": profile_info,
                "connected_user_email": profile_info.get("email"),
                "storage_quota": await self._get_storage_quota(
                    access_token, service_type
                ),
            }
            integration.status = "active"

            await session.commit()
            await session.refresh(oauth_token)

            # Initialize data sources
            await self._initialize_data_sources(integration, oauth_token, service_type)

            logger.info(
                f"OAuth completed for {service_type} user {profile_info.get('email')}"
            )
            return oauth_token

        except Exception as e:
            logger.error(f"Error completing OAuth flow: {e}")
            await session.rollback()
            raise
        finally:
            if not self.session:
                await session.close()

    async def fetch_files(
        self,
        integration_id: str,
        service_type: str,
        folder_id: Optional[str] = None,
        query: Optional[str] = None,
        max_results: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Fetch files from Google Drive or OneDrive.

        Args:
            integration_id: Integration ID
            service_type: 'drive' or 'onedrive'
            folder_id: Specific folder to search in
            query: Search query
            max_results: Maximum files to return

        Returns:
            List of file dictionaries
        """
        session = self.session or await get_db_session().__anext__()

        try:
            # Get valid token
            token = await self._get_valid_token(session, integration_id)
            access_token = self._decrypt_token(token.access_token_encrypted)

            if service_type == "drive":
                files = await self._fetch_drive_files(
                    access_token, folder_id, query, max_results
                )
            else:  # onedrive
                files = await self._fetch_onedrive_files(
                    access_token, folder_id, query, max_results
                )

            # Log file fetch
            await self._log_operation(
                integration_id,
                None,
                "fetch_files",
                f"Fetched {len(files)} files from {service_type}",
                {
                    "service_type": service_type,
                    "file_count": len(files),
                    "folder_id": folder_id,
                    "query": query,
                },
            )

            return files

        except Exception as e:
            logger.error(f"Error fetching files: {e}")
            raise
        finally:
            if not self.session:
                await session.close()

    async def extract_file_content(
        self, integration_id: str, service_type: str, file_id: str
    ) -> Dict[str, Any]:
        """Extract content from a document file.

        Args:
            integration_id: Integration ID
            service_type: 'drive' or 'onedrive'
            file_id: File ID to extract content from

        Returns:
            Extracted content and metadata
        """
        session = self.session or await get_db_session().__anext__()

        try:
            # Get valid token
            token = await self._get_valid_token(session, integration_id)
            access_token = self._decrypt_token(token.access_token_encrypted)

            # Get file metadata first
            if service_type == "drive":
                file_metadata = await self._get_drive_file_metadata(
                    access_token, file_id
                )
                file_content = await self._download_drive_file(
                    access_token, file_id, file_metadata
                )
            else:  # onedrive
                file_metadata = await self._get_onedrive_file_metadata(
                    access_token, file_id
                )
                file_content = await self._download_onedrive_file(
                    access_token, file_id, file_metadata
                )

            # Extract text content based on file type
            extracted_content = await self._extract_text_content(
                file_content,
                file_metadata.get("mimeType") or file_metadata.get("mime_type"),
                file_metadata.get("name", ""),
            )

            result = {
                "file_id": file_id,
                "name": file_metadata.get("name"),
                "mime_type": file_metadata.get("mimeType")
                or file_metadata.get("mime_type"),
                "size": file_metadata.get("size", 0),
                "modified_time": file_metadata.get("modifiedTime")
                or file_metadata.get("lastModifiedDateTime"),
                "content": extracted_content.get("text", ""),
                "metadata": extracted_content.get("metadata", {}),
                "extraction_method": extracted_content.get("method", "unknown"),
                "word_count": len(extracted_content.get("text", "").split()),
                "service_type": service_type,
            }

            # Log content extraction
            await self._log_operation(
                integration_id,
                None,
                "extract_content",
                f"Extracted content from {file_metadata.get('name')}",
                {
                    "file_id": file_id,
                    "file_name": file_metadata.get("name"),
                    "content_length": len(extracted_content.get("text", "")),
                    "extraction_method": extracted_content.get("method"),
                },
            )

            return result

        except Exception as e:
            logger.error(f"Error extracting file content: {e}")
            raise
        finally:
            if not self.session:
                await session.close()

    async def track_file_changes(
        self, integration_id: str, service_type: str, webhook_url: str
    ) -> Dict[str, Any]:
        """Set up real-time file change notifications.

        Args:
            integration_id: Integration ID
            service_type: 'drive' or 'onedrive'
            webhook_url: URL to receive change notifications

        Returns:
            Notification configuration
        """
        session = self.session or await get_db_session().__anext__()

        try:
            # Get valid token
            token = await self._get_valid_token(session, integration_id)
            access_token = self._decrypt_token(token.access_token_encrypted)

            if service_type == "drive":
                notification_config = await self._setup_drive_notifications(
                    access_token, webhook_url
                )
            else:  # onedrive
                notification_config = await self._setup_onedrive_notifications(
                    access_token, webhook_url
                )

            # Update integration with notification config
            integration_query = select(Integration).where(
                Integration.id == integration_id
            )
            result = await session.execute(integration_query)
            integration = result.scalar_one()

            integration.webhook_url = webhook_url
            integration.integration_metadata = {
                **(integration.integration_metadata or {}),
                "notifications": notification_config,
                "real_time_enabled": True,
            }

            await session.commit()

            # Log notification setup
            await self._log_operation(
                integration_id,
                None,
                "setup_notifications",
                f"Set up change notifications for {service_type}",
                {
                    "webhook_url": webhook_url,
                    "notification_config": notification_config,
                },
            )

            return notification_config

        except Exception as e:
            logger.error(f"Error setting up file change tracking: {e}")
            raise
        finally:
            if not self.session:
                await session.close()

    async def calculate_document_relevance(
        self,
        integration_id: str,
        file_data: Dict[str, Any],
        query_context: Optional[str] = None,
    ) -> float:
        """Calculate relevance score for a document.

        Args:
            integration_id: Integration ID
            file_data: File metadata and content
            query_context: Optional query context for relevance

        Returns:
            Relevance score between 0.0 and 1.0
        """
        try:
            score = 0.0

            # Base factors
            name = file_data.get("name", "").lower()
            content = file_data.get("content", "").lower()
            file_type = file_data.get("mime_type", "")
            modified_time = file_data.get("modified_time")

            # Recency factor (30%)
            if modified_time:
                try:
                    if isinstance(modified_time, str):
                        mod_date = datetime.fromisoformat(
                            modified_time.replace("Z", "+00:00")
                        )
                    else:
                        mod_date = modified_time

                    days_old = (datetime.now(timezone.utc) - mod_date).days
                    recency_score = max(0, 1 - (days_old / 365))  # Decay over a year
                    score += recency_score * 0.3
                except Exception:
                    score += 0.1  # Small base score if date parsing fails

            # File type relevance (20%)
            important_types = ["pdf", "docx", "txt", "md", "gdoc", "gsheet", "gslides"]
            file_ext = name.split(".")[-1] if "." in name else ""
            if any(ft in file_type or ft in file_ext for ft in important_types):
                score += 0.2

            # Content length factor (10%)
            content_length = len(content)
            if content_length > 100:  # Has substantial content
                content_score = min(1.0, content_length / 10000)  # Cap at 10k chars
                score += content_score * 0.1

            # Query context matching (40%)
            if query_context:
                query_terms = query_context.lower().split()
                name_matches = sum(1 for term in query_terms if term in name)
                content_matches = sum(1 for term in query_terms if term in content)

                name_score = min(1.0, name_matches / len(query_terms))
                content_score = min(
                    1.0, content_matches / (len(query_terms) * 10)
                )  # More lenient for content

                score += name_score * 0.2 + content_score * 0.2
            else:
                score += 0.2  # Base score when no query context

            return min(1.0, score)

        except Exception as e:
            logger.error(f"Error calculating document relevance: {e}")
            return 0.5  # Default moderate relevance

    # Helper methods

    async def _get_valid_token(
        self, session: AsyncSession, integration_id: str
    ) -> OAuthToken:
        """Get a valid OAuth token, refreshing if necessary."""
        query = (
            select(OAuthToken)
            .where(
                and_(
                    OAuthToken.integration_id == integration_id,
                    OAuthToken.status == "active",
                )
            )
            .order_by(desc(OAuthToken.created_at))
        )

        result = await session.execute(query)
        token = result.scalar_one_or_none()

        if not token:
            raise ValueError("No valid OAuth token found")

        # Check if token needs refresh
        if token.expires_at and datetime.now(timezone.utc) >= token.expires_at:
            if token.refresh_token_encrypted:
                token = await self._refresh_token(session, token)
            else:
                raise ValueError("OAuth token expired and no refresh token available")

        return token

    async def _refresh_token(
        self, session: AsyncSession, token: OAuthToken
    ) -> OAuthToken:
        """Refresh an expired OAuth token."""
        # TODO: Implement token refresh logic
        raise NotImplementedError("Token refresh not yet implemented")

    async def _get_user_profile(
        self, access_token: str, service_type: str
    ) -> Dict[str, Any]:
        """Get user profile information from the service."""
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            if service_type == "drive":
                url = "https://www.googleapis.com/oauth2/v2/userinfo"
            else:  # onedrive
                url = f"{self.onedrive_base_url}/me"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()

                        if service_type == "drive":
                            return {
                                "id": data.get("id"),
                                "email": data.get("email"),
                                "username": data.get("name"),
                            }
                        else:  # onedrive
                            return {
                                "id": data.get("id"),
                                "email": data.get("mail")
                                or data.get("userPrincipalName"),
                                "username": data.get("displayName"),
                            }
                    else:
                        logger.error(f"Failed to get user profile: {response.status}")
                        return {}

        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return {}

    async def _get_storage_quota(
        self, access_token: str, service_type: str
    ) -> Dict[str, Any]:
        """Get storage quota information."""
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            if service_type == "drive":
                url = f"{self.drive_base_url}/about?fields=storageQuota"
            else:  # onedrive
                url = f"{self.onedrive_base_url}/me/drive"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()

                        if service_type == "drive":
                            quota = data.get("storageQuota", {})
                            return {
                                "limit": int(quota.get("limit", 0)),
                                "used": int(quota.get("usage", 0)),
                                "available": int(quota.get("limit", 0))
                                - int(quota.get("usage", 0)),
                            }
                        else:  # onedrive
                            quota = data.get("quota", {})
                            return {
                                "limit": quota.get("total", 0),
                                "used": quota.get("used", 0),
                                "available": quota.get("remaining", 0),
                            }
                    else:
                        return {"limit": 0, "used": 0, "available": 0}

        except Exception as e:
            logger.error(f"Error getting storage quota: {e}")
            return {"limit": 0, "used": 0, "available": 0}

    async def _fetch_drive_files(
        self,
        access_token: str,
        folder_id: Optional[str],
        query: Optional[str],
        max_results: int,
    ) -> List[Dict[str, Any]]:
        """Fetch files from Google Drive."""
        headers = {"Authorization": f"Bearer {access_token}"}
        files = []

        try:
            url = f"{self.drive_base_url}/files"
            params = {
                "fields": "nextPageToken,files(id,name,mimeType,size,modifiedTime,parents,webViewLink,permissions)",
                "pageSize": min(max_results, 1000),
            }

            # Build query
            q_parts = []
            if folder_id:
                q_parts.append(f"'{folder_id}' in parents")
            if query:
                q_parts.append(
                    f"name contains '{query}' or fullText contains '{query}'"
                )

            if q_parts:
                params["q"] = " and ".join(q_parts)

            page_token = None
            while len(files) < max_results:
                if page_token:
                    params["pageToken"] = page_token

                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url, headers=headers, params=params
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            batch_files = data.get("files", [])

                            for file_data in batch_files:
                                processed_file = self._process_drive_file(file_data)
                                files.append(processed_file)

                                if len(files) >= max_results:
                                    break

                            page_token = data.get("nextPageToken")
                            if not page_token:
                                break
                        else:
                            break

        except Exception as e:
            logger.error(f"Error fetching Drive files: {e}")

        return files

    async def _fetch_onedrive_files(
        self,
        access_token: str,
        folder_id: Optional[str],
        query: Optional[str],
        max_results: int,
    ) -> List[Dict[str, Any]]:
        """Fetch files from OneDrive."""
        headers = {"Authorization": f"Bearer {access_token}"}
        files = []

        try:
            if folder_id:
                url = f"{self.onedrive_base_url}/me/drive/items/{folder_id}/children"
            else:
                url = f"{self.onedrive_base_url}/me/drive/root/children"

            params = {"$top": min(max_results, 1000)}

            if query:
                # Use search endpoint for OneDrive
                url = f"{self.onedrive_base_url}/me/drive/root/search(q='{query}')"

            skip = 0
            while len(files) < max_results:
                params["$skip"] = skip

                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url, headers=headers, params=params
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            batch_files = data.get("value", [])

                            if not batch_files:
                                break

                            for file_data in batch_files:
                                processed_file = self._process_onedrive_file(file_data)
                                files.append(processed_file)

                                if len(files) >= max_results:
                                    break

                            skip += len(batch_files)
                        else:
                            break

        except Exception as e:
            logger.error(f"Error fetching OneDrive files: {e}")

        return files

    def _process_drive_file(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Google Drive file data into standard format."""
        return {
            "id": file_data.get("id"),
            "name": file_data.get("name"),
            "mime_type": file_data.get("mimeType"),
            "size": int(file_data.get("size", 0)) if file_data.get("size") else 0,
            "modified_time": file_data.get("modifiedTime"),
            "parents": file_data.get("parents", []),
            "web_view_link": file_data.get("webViewLink"),
            "permissions": file_data.get("permissions", []),
            "service_type": "drive",
        }

    def _process_onedrive_file(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process OneDrive file data into standard format."""
        return {
            "id": file_data.get("id"),
            "name": file_data.get("name"),
            "mime_type": (
                file_data.get("file", {}).get("mimeType")
                if file_data.get("file")
                else "folder"
            ),
            "size": file_data.get("size", 0),
            "modified_time": file_data.get("lastModifiedDateTime"),
            "web_view_link": file_data.get("webUrl"),
            "parent_id": file_data.get("parentReference", {}).get("id"),
            "service_type": "onedrive",
        }

    async def _extract_text_content(
        self, file_content: bytes, mime_type: str, filename: str
    ) -> Dict[str, Any]:
        """Extract text content from file bytes."""
        try:
            # For now, implement basic text extraction
            # In production, would use libraries like PyPDF2, python-docx, etc.

            if mime_type in ["text/plain", "text/markdown", "text/html"]:
                text = file_content.decode("utf-8", errors="ignore")
                return {
                    "text": text,
                    "method": "direct_decode",
                    "metadata": {"encoding": "utf-8"},
                }

            elif "pdf" in mime_type:
                # TODO: Implement PDF text extraction with PyPDF2 or similar
                return {
                    "text": "[PDF content - extraction not implemented]",
                    "method": "pdf_placeholder",
                    "metadata": {"file_type": "pdf"},
                }

            elif "word" in mime_type or "docx" in mime_type:
                # TODO: Implement DOCX text extraction with python-docx
                return {
                    "text": "[DOCX content - extraction not implemented]",
                    "method": "docx_placeholder",
                    "metadata": {"file_type": "docx"},
                }

            else:
                return {
                    "text": f"[{mime_type} content - extraction not supported]",
                    "method": "unsupported",
                    "metadata": {"mime_type": mime_type},
                }

        except Exception as e:
            logger.error(f"Error extracting text content: {e}")
            return {
                "text": "[Content extraction failed]",
                "method": "error",
                "metadata": {"error": str(e)},
            }

    def _encrypt_token(self, token: str) -> str:
        """Encrypt token for secure storage."""
        # TODO: Implement proper encryption
        return token

    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt token from storage."""
        # TODO: Implement proper decryption
        return encrypted_token

    async def _initialize_data_sources(
        self, integration: Integration, oauth_token: OAuthToken, service_type: str
    ) -> None:
        """Initialize data sources for the integration."""
        session = self.session or await get_db_session().__anext__()

        try:
            # Create root data source
            root_source = DataSource(
                integration_id=integration.id,
                source_type="drive" if service_type == "drive" else "folder",
                external_id="root",
                name=f"{service_type.title()} Root",
                description=f"Root folder for {service_type}",
                source_metadata={
                    "service_type": service_type,
                    "user_email": oauth_token.external_email,
                },
                sync_frequency="hourly",
                privacy_level="standard",
            )
            session.add(root_source)

            await session.commit()
            logger.info(
                f"Initialized data sources for {service_type} integration {integration.id}"
            )

        except Exception as e:
            logger.error(f"Error initializing data sources: {e}")
            await session.rollback()
        finally:
            if not self.session:
                await session.close()

    # Placeholder methods for file operations (to be implemented)

    async def _get_drive_file_metadata(
        self, access_token: str, file_id: str
    ) -> Dict[str, Any]:
        """Get Google Drive file metadata."""
        # TODO: Implement
        return {"id": file_id, "name": "placeholder", "mimeType": "text/plain"}

    async def _get_onedrive_file_metadata(
        self, access_token: str, file_id: str
    ) -> Dict[str, Any]:
        """Get OneDrive file metadata."""
        # TODO: Implement
        return {"id": file_id, "name": "placeholder", "mime_type": "text/plain"}

    async def _download_drive_file(
        self, access_token: str, file_id: str, metadata: Dict[str, Any]
    ) -> bytes:
        """Download file from Google Drive."""
        # TODO: Implement
        return b"placeholder content"

    async def _download_onedrive_file(
        self, access_token: str, file_id: str, metadata: Dict[str, Any]
    ) -> bytes:
        """Download file from OneDrive."""
        # TODO: Implement
        return b"placeholder content"

    async def _setup_drive_notifications(
        self, access_token: str, webhook_url: str
    ) -> Dict[str, Any]:
        """Set up Google Drive change notifications."""
        # TODO: Implement Push notifications
        return {"type": "web_hook", "address": webhook_url}

    async def _setup_onedrive_notifications(
        self, access_token: str, webhook_url: str
    ) -> Dict[str, Any]:
        """Set up OneDrive change notifications."""
        # TODO: Implement webhooks
        return {"notification_url": webhook_url}

    async def _log_operation(
        self,
        integration_id: str,
        user_id: Optional[str],
        operation: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an integration operation."""
        session = self.session or await get_db_session().__anext__()

        try:
            log_entry = IntegrationLog(
                integration_id=integration_id,
                user_id=user_id,
                log_level="INFO",
                operation=operation,
                message=message,
                log_metadata=metadata or {},
            )

            session.add(log_entry)
            await session.commit()

        except Exception as e:
            logger.error(f"Error logging operation: {e}")
        finally:
            if not self.session:
                await session.close()

# Singleton instance
document_integration_service = DocumentIntegrationService()
