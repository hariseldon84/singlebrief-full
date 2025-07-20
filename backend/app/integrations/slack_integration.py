"""Slack Integration Service for SingleBrief.

This module implements the Slack integration connector using the Integration Hub
framework, providing OAuth, message retrieval, real-time streaming, and search.
"""

from typing import Any, Dict, List, Optional, Tuple

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlencode, urlparse

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

class SlackIntegrationService:
    """Service for Slack workspace integration and data retrieval."""

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
        self.integration_hub = IntegrationHubService(session)

        # Slack API configuration
        self.base_url = "https://slack.com/api"
        self.oauth_url = "https://slack.com/oauth/v2/authorize"
        self.token_url = "https://slack.com/api/oauth.v2.access"

        # Required scopes for comprehensive access
        self.required_scopes = [
            "channels:read",  # Read channel info
            "channels:history",  # Read channel messages
            "groups:read",  # Read private channel info
            "groups:history",  # Read private channel messages
            "im:read",  # Read DM info
            "im:history",  # Read DM messages
            "mpim:read",  # Read group DM info
            "mpim:history",  # Read group DM messages
            "users:read",  # Read user info
            "team:read",  # Read workspace info
            "files:read",  # Read file info
            "search:read",  # Search messages
            "reactions:read",  # Read reactions
            "pins:read",  # Read pinned messages
            "usergroups:read",  # Read user groups
            "emoji:read",  # Read custom emoji
        ]

        # Rate limits (Slack Tier 1 limits)
        self.rate_limits = {
            "web_api": 1,  # 1 request per second for most methods
            "conversations": 1,  # 1 request per second for conversations
            "users": 50,  # 50 requests per minute for users methods
            "search": 1,  # 1 request per second for search
            "files": 20,  # 20 requests per minute for files
        }

    async def register_slack_connector(self) -> str:
        """Register the Slack connector in the Integration Hub.

        Returns:
            Connector ID for Slack integration
        """
        try:
            config_schema = {
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "Slack app client ID",
                    },
                    "client_secret": {
                        "type": "string",
                        "description": "Slack app client secret",
                    },
                    "signing_secret": {
                        "type": "string",
                        "description": "Slack app signing secret for webhook verification",
                    },
                    "channels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific channels to monitor (empty for all)",
                    },
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keywords to monitor for alerts",
                    },
                    "sync_frequency": {
                        "type": "string",
                        "enum": ["realtime", "hourly", "daily"],
                        "default": "realtime",
                    },
                    "include_files": {
                        "type": "boolean",
                        "default": true,
                        "description": "Whether to sync file attachments",
                    },
                    "include_reactions": {
                        "type": "boolean",
                        "default": true,
                        "description": "Whether to sync message reactions",
                    },
                    "thread_depth": {
                        "type": "integer",
                        "default": 50,
                        "description": "Maximum thread depth to sync",
                    },
                },
                "required": ["client_id", "client_secret", "signing_secret"],
            }

            connector = await self.integration_hub.register_connector(
                connector_type="slack",
                name="Slack Workspace Integration",
                version="1.0.0",
                developer="SingleBrief",
                capabilities=[
                    "read_messages",
                    "read_channels",
                    "read_users",
                    "read_files",
                    "search_messages",
                    "real_time_events",
                    "thread_tracking",
                    "reaction_tracking",
                ],
                config_schema=config_schema,
                description="Integration for Slack workspaces with real-time message streaming",
                required_scopes=self.required_scopes,
                supported_auth_types=["oauth2"],
                default_rate_limit_hour=3600,  # 1 per second
                default_rate_limit_day=86400,  # Roughly 1 per second daily
                burst_limit=10,
                is_official=True,
                is_verified=True,
            )

            logger.info(f"Registered Slack connector: {connector.id}")
            return connector.id

        except Exception as e:
            logger.error(f"Error registering Slack connector: {e}")
            raise

    async def initiate_oauth_flow(
        self,
        organization_id: str,
        user_id: str,
        redirect_uri: str,
        state: Optional[str] = None,
    ) -> str:
        """Initiate Slack OAuth 2.0 authorization flow.

        Args:
            organization_id: Organization ID
            user_id: User ID initiating OAuth
            redirect_uri: OAuth redirect URI
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL for user to visit
        """
        try:
            # Get connector configuration
            session = self.session or await get_db_session().__anext__()

            integration_query = select(Integration).where(
                and_(
                    Integration.organization_id == organization_id,
                    Integration.service_type == "slack",
                )
            )
            result = await session.execute(integration_query)
            integration = result.scalar_one_or_none()

            if not integration:
                raise ValueError("Slack integration not configured for organization")

            client_id = integration.config.get("client_id")
            if not client_id:
                raise ValueError("Slack client_id not configured")

            # Generate state if not provided
            if not state:
                state = hashlib.sha256(
                    f"{organization_id}:{user_id}:{datetime.now().isoformat()}".encode()
                ).hexdigest()

            # Build authorization URL
            auth_params = {
                "client_id": client_id,
                "scope": ",".join(self.required_scopes),
                "redirect_uri": redirect_uri,
                "state": state,
                "response_type": "code",
            }

            auth_url = f"{self.oauth_url}?{urlencode(auth_params)}"

            # Log OAuth initiation
            await self._log_operation(
                integration.id,
                user_id,
                "oauth_initiate",
                f"OAuth flow initiated for user {user_id}",
                {"redirect_uri": redirect_uri, "state": state},
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
        authorization_code: str,
        redirect_uri: str,
    ) -> OAuthToken:
        """Complete Slack OAuth flow and store tokens.

        Args:
            organization_id: Organization ID
            user_id: User ID completing OAuth
            authorization_code: Authorization code from Slack
            redirect_uri: OAuth redirect URI

        Returns:
            Created OAuthToken instance
        """
        session = self.session or await get_db_session().__anext__()

        try:
            # Get integration and client credentials
            integration_query = select(Integration).where(
                and_(
                    Integration.organization_id == organization_id,
                    Integration.service_type == "slack",
                )
            )
            result = await session.execute(integration_query)
            integration = result.scalar_one_or_none()

            if not integration:
                raise ValueError("Slack integration not found")

            client_id = integration.config.get("client_id")
            client_secret = integration.config.get("client_secret")

            if not client_id or not client_secret:
                raise ValueError("Slack client credentials not configured")

            # Exchange authorization code for access token
            token_data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "code": authorization_code,
                "redirect_uri": redirect_uri,
            }

            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(
                    self.token_url, data=token_data
                ) as response:
                    response_data = await response.json()

                    if not response_data.get("ok"):
                        error = response_data.get("error", "Unknown error")
                        raise ValueError(f"OAuth token exchange failed: {error}")

            # Extract token information
            access_token = response_data["access_token"]
            token_type = response_data.get("token_type", "Bearer")
            scope = response_data.get("scope", "")
            team_info = response_data.get("team", {})
            authed_user = response_data.get("authed_user", {})

            # Encrypt and store token
            # Note: In production, implement proper encryption
            encrypted_token = self._encrypt_token(access_token)

            oauth_token = OAuthToken(
                integration_id=integration.id,
                user_id=user_id,
                access_token_encrypted=encrypted_token,
                token_type=token_type,
                scopes=scope.split(",") if scope else [],
                external_user_id=authed_user.get("id"),
                external_username=authed_user.get("username"),
                external_email=authed_user.get("email"),
                encryption_key_id="default",  # Use proper key management
                encryption_algorithm="AES-256-GCM",
            )

            session.add(oauth_token)

            # Update integration with team information
            integration.integration_metadata = {
                **(integration.integration_metadata or {}),
                "team_id": team_info.get("id"),
                "team_name": team_info.get("name"),
                "team_domain": team_info.get("domain"),
                "connected_user_id": authed_user.get("id"),
                "connected_user_name": authed_user.get("username"),
            }
            integration.status = "active"

            await session.commit()
            await session.refresh(oauth_token)

            # Log successful OAuth completion
            await self._log_operation(
                integration.id,
                user_id,
                "oauth_complete",
                f"OAuth completed for team {team_info.get('name')}",
                {
                    "team_id": team_info.get("id"),
                    "scopes": oauth_token.scopes,
                    "user_id": authed_user.get("id"),
                },
            )

            # Initialize data sources (channels, etc.)
            await self._initialize_data_sources(integration, oauth_token)

            logger.info(
                f"OAuth completed for user {user_id} in team {team_info.get('name')}"
            )
            return oauth_token

        except Exception as e:
            logger.error(f"Error completing OAuth flow: {e}")
            await session.rollback()
            raise
        finally:
            if not self.session:
                await session.close()

    async def fetch_channels(
        self, integration_id: str, include_private: bool = True
    ) -> List[Dict[str, Any]]:
        """Fetch all accessible channels from Slack workspace.

        Args:
            integration_id: Integration ID
            include_private: Whether to include private channels

        Returns:
            List of channel information dictionaries
        """
        session = self.session or await get_db_session().__anext__()

        try:
            # Get OAuth token
            token = await self._get_valid_token(session, integration_id)
            access_token = self._decrypt_token(token.access_token_encrypted)

            channels = []
            cursor = None

            # Fetch public channels
            while True:
                params = {"types": "public_channel", "limit": 200}
                if cursor:
                    params["cursor"] = cursor

                response = await self._make_api_call(
                    access_token, "conversations.list", params
                )

                if not response.get("ok"):
                    raise ValueError(
                        f"Failed to fetch channels: {response.get('error')}"
                    )

                channels.extend(response.get("channels", []))

                cursor = response.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break

            # Fetch private channels if requested
            if include_private:
                cursor = None
                while True:
                    params = {"types": "private_channel", "limit": 200}
                    if cursor:
                        params["cursor"] = cursor

                    response = await self._make_api_call(
                        access_token, "conversations.list", params
                    )

                    if response.get("ok"):
                        channels.extend(response.get("channels", []))
                        cursor = response.get("response_metadata", {}).get(
                            "next_cursor"
                        )
                        if not cursor:
                            break
                    else:
                        # May not have access to private channels
                        break

            # Log channel fetch
            await self._log_operation(
                integration_id,
                None,
                "fetch_channels",
                f"Fetched {len(channels)} channels",
                {"channel_count": len(channels), "include_private": include_private},
            )

            return channels

        except Exception as e:
            logger.error(f"Error fetching channels: {e}")
            raise
        finally:
            if not self.session:
                await session.close()

    async def fetch_messages(
        self,
        integration_id: str,
        channel_id: str,
        limit: int = 100,
        oldest: Optional[str] = None,
        latest: Optional[str] = None,
        include_threads: bool = True,
    ) -> List[Dict[str, Any]]:
        """Fetch messages from a Slack channel.

        Args:
            integration_id: Integration ID
            channel_id: Slack channel ID
            limit: Maximum number of messages to fetch
            oldest: Oldest timestamp to fetch (inclusive)
            latest: Latest timestamp to fetch (exclusive)
            include_threads: Whether to fetch thread replies

        Returns:
            List of message dictionaries
        """
        session = self.session or await get_db_session().__anext__()

        try:
            # Get OAuth token
            token = await self._get_valid_token(session, integration_id)
            access_token = self._decrypt_token(token.access_token_encrypted)

            # Fetch messages
            params = {"channel": channel_id, "limit": min(limit, 1000)}  # Slack maximum
            if oldest:
                params["oldest"] = oldest
            if latest:
                params["latest"] = latest

            response = await self._make_api_call(
                access_token, "conversations.history", params
            )

            if not response.get("ok"):
                raise ValueError(f"Failed to fetch messages: {response.get('error')}")

            messages = response.get("messages", [])

            # Fetch thread replies if requested
            if include_threads:
                for message in messages:
                    if message.get("thread_ts") and message.get("reply_count", 0) > 0:
                        thread_replies = await self._fetch_thread_replies(
                            access_token, channel_id, message["thread_ts"]
                        )
                        message["replies"] = thread_replies

            # Log message fetch
            await self._log_operation(
                integration_id,
                None,
                "fetch_messages",
                f"Fetched {len(messages)} messages from channel {channel_id}",
                {
                    "channel_id": channel_id,
                    "message_count": len(messages),
                    "include_threads": include_threads,
                },
            )

            return messages

        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            raise
        finally:
            if not self.session:
                await session.close()

    async def search_messages(
        self,
        integration_id: str,
        query: str,
        sort: str = "timestamp",
        sort_dir: str = "desc",
        count: int = 20,
    ) -> Dict[str, Any]:
        """Search messages across the Slack workspace.

        Args:
            integration_id: Integration ID
            query: Search query
            sort: Sort field (timestamp, score)
            sort_dir: Sort direction (asc, desc)
            count: Number of results to return

        Returns:
            Search results dictionary
        """
        session = self.session or await get_db_session().__anext__()

        try:
            # Get OAuth token
            token = await self._get_valid_token(session, integration_id)
            access_token = self._decrypt_token(token.access_token_encrypted)

            # Search messages
            params = {
                "query": query,
                "sort": sort,
                "sort_dir": sort_dir,
                "count": min(count, 1000),  # Slack maximum
            }

            response = await self._make_api_call(
                access_token, "search.messages", params
            )

            if not response.get("ok"):
                raise ValueError(f"Search failed: {response.get('error')}")

            # Log search
            await self._log_operation(
                integration_id,
                None,
                "search_messages",
                f"Searched messages: '{query}'",
                {
                    "query": query,
                    "result_count": response.get("messages", {}).get("total", 0),
                },
            )

            return response.get("messages", {})

        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            raise
        finally:
            if not self.session:
                await session.close()

    async def setup_real_time_events(
        self, integration_id: str, event_url: str
    ) -> Dict[str, Any]:
        """Setup real-time event subscriptions for Slack Events API.

        Args:
            integration_id: Integration ID
            event_url: URL to receive event callbacks

        Returns:
            Event subscription configuration
        """
        session = self.session or await get_db_session().__anext__()

        try:
            # Get integration
            integration_query = select(Integration).where(
                Integration.id == integration_id
            )
            result = await session.execute(integration_query)
            integration = result.scalar_one_or_none()

            if not integration:
                raise ValueError("Integration not found")

            # Update webhook configuration
            integration.webhook_url = event_url
            integration.webhook_secret = integration.config.get("signing_secret")

            # Update metadata with event subscriptions
            event_types = [
                "message.channels",  # Messages in public channels
                "message.groups",  # Messages in private channels
                "message.im",  # Direct messages
                "message.mpim",  # Group direct messages
                "member_joined_channel",
                "member_left_channel",
                "channel_created",
                "channel_deleted",
                "channel_rename",
                "file_shared",
                "reaction_added",
                "reaction_removed",
                "pin_added",
                "pin_removed",
            ]

            integration.integration_metadata = {
                **(integration.integration_metadata or {}),
                "event_subscriptions": event_types,
                "webhook_url": event_url,
                "real_time_enabled": True,
            }

            await session.commit()

            # Log event setup
            await self._log_operation(
                integration_id,
                None,
                "setup_events",
                f"Configured real-time events for {len(event_types)} event types",
                {"event_url": event_url, "event_types": event_types},
            )

            return {
                "webhook_url": event_url,
                "event_types": event_types,
                "signing_secret": integration.webhook_secret,
            }

        except Exception as e:
            logger.error(f"Error setting up real-time events: {e}")
            raise
        finally:
            if not self.session:
                await session.close()

    async def process_webhook_event(
        self, integration_id: str, event_data: Dict[str, Any], headers: Dict[str, str]
    ) -> bool:
        """Process incoming webhook event from Slack.

        Args:
            integration_id: Integration ID
            event_data: Event payload from Slack
            headers: Request headers for verification

        Returns:
            True if event was processed successfully
        """
        session = self.session or await get_db_session().__anext__()

        try:
            # Verify webhook signature
            if not await self._verify_webhook_signature(
                integration_id, event_data, headers
            ):
                raise ValueError("Invalid webhook signature")

            # Handle URL verification challenge
            if event_data.get("type") == "url_verification":
                return {"challenge": event_data.get("challenge")}

            # Process the event
            event_type = event_data.get("event", {}).get("type")
            event_subtype = event_data.get("event", {}).get("subtype")

            if event_type in ["message", "app_mention"]:
                await self._process_message_event(integration_id, event_data)
            elif event_type in ["member_joined_channel", "member_left_channel"]:
                await self._process_membership_event(integration_id, event_data)
            elif event_type in ["channel_created", "channel_deleted", "channel_rename"]:
                await self._process_channel_event(integration_id, event_data)
            elif event_type in ["reaction_added", "reaction_removed"]:
                await self._process_reaction_event(integration_id, event_data)
            elif event_type == "file_shared":
                await self._process_file_event(integration_id, event_data)

            # Log event processing
            await self._log_operation(
                integration_id,
                None,
                "webhook_event",
                f"Processed {event_type} event",
                {"event_type": event_type, "event_subtype": event_subtype},
            )

            return True

        except Exception as e:
            logger.error(f"Error processing webhook event: {e}")
            return False
        finally:
            if not self.session:
                await session.close()

    # Helper methods

    async def _get_valid_token(
        self, session: AsyncSession, integration_id: str
    ) -> OAuthToken:
        """Get a valid OAuth token for the integration."""
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

        # Check if token is expired
        if token.expires_at and datetime.now(timezone.utc) >= token.expires_at:
            raise ValueError("OAuth token expired")

        return token

    async def _make_api_call(
        self, access_token: str, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an authenticated API call to Slack."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        url = f"{self.base_url}/{method}"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, headers=headers, data=params or {}
            ) as response:
                return await response.json()

    async def _fetch_thread_replies(
        self, access_token: str, channel_id: str, thread_ts: str
    ) -> List[Dict[str, Any]]:
        """Fetch replies in a message thread."""
        params = {"channel": channel_id, "ts": thread_ts}

        response = await self._make_api_call(
            access_token, "conversations.replies", params
        )

        if response.get("ok"):
            # Remove the parent message from replies
            messages = response.get("messages", [])
            return messages[1:] if len(messages) > 1 else []

        return []

    def _encrypt_token(self, token: str) -> str:
        """Encrypt OAuth token for secure storage."""
        # TODO: Implement proper encryption using app.core.security
        # For now, return as-is (NOT FOR PRODUCTION)
        return token

    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt OAuth token from storage."""
        # TODO: Implement proper decryption using app.core.security
        # For now, return as-is (NOT FOR PRODUCTION)
        return encrypted_token

    async def _verify_webhook_signature(
        self, integration_id: str, event_data: Dict[str, Any], headers: Dict[str, str]
    ) -> bool:
        """Verify Slack webhook signature."""
        # TODO: Implement proper signature verification
        # For now, return True (NOT FOR PRODUCTION)
        return True

    async def _initialize_data_sources(
        self, integration: Integration, oauth_token: OAuthToken
    ) -> None:
        """Initialize data sources (channels) for the integration."""
        session = self.session or await get_db_session().__anext__()

        try:
            # Fetch channels and create data sources
            channels = await self.fetch_channels(integration.id)

            for channel in channels:
                data_source = DataSource(
                    integration_id=integration.id,
                    source_type="channel",
                    external_id=channel["id"],
                    name=channel["name"],
                    description=channel.get("purpose", {}).get("value"),
                    source_metadata={
                        "is_private": channel.get("is_private", False),
                        "is_archived": channel.get("is_archived", False),
                        "member_count": channel.get("num_members", 0),
                        "created": channel.get("created"),
                        "creator": channel.get("creator"),
                        "topic": channel.get("topic", {}).get("value"),
                    },
                    sync_frequency="realtime",
                    privacy_level=(
                        "standard" if not channel.get("is_private") else "sensitive"
                    ),
                )

                session.add(data_source)

            await session.commit()
            logger.info(
                f"Initialized {len(channels)} data sources for integration {integration.id}"
            )

        except Exception as e:
            logger.error(f"Error initializing data sources: {e}")
            await session.rollback()
        finally:
            if not self.session:
                await session.close()

    async def _process_message_event(
        self, integration_id: str, event_data: Dict[str, Any]
    ) -> None:
        """Process incoming message events."""
        # TODO: Implement message processing and storage
        # This would involve parsing the message, extracting metadata,
        # and storing it in the appropriate data structures for search/retrieval
        pass

    async def _process_membership_event(
        self, integration_id: str, event_data: Dict[str, Any]
    ) -> None:
        """Process channel membership change events."""
        # TODO: Implement membership tracking
        pass

    async def _process_channel_event(
        self, integration_id: str, event_data: Dict[str, Any]
    ) -> None:
        """Process channel creation/deletion/rename events."""
        # TODO: Implement channel change tracking
        pass

    async def _process_reaction_event(
        self, integration_id: str, event_data: Dict[str, Any]
    ) -> None:
        """Process reaction add/remove events."""
        # TODO: Implement reaction tracking
        pass

    async def _process_file_event(
        self, integration_id: str, event_data: Dict[str, Any]
    ) -> None:
        """Process file sharing events."""
        # TODO: Implement file tracking
        pass

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

# Singleton instance for easy access
slack_integration_service = SlackIntegrationService()
