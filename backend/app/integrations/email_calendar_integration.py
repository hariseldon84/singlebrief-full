"""Email and Calendar Integration Service for SingleBrief.

This module implements Gmail/Outlook email and calendar integration using OAuth 2.0,
providing message retrieval, calendar event access, and real-time monitoring.
"""

from typing import Any, Dict, List, Optional, Tuple

import base64
import email
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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

class EmailCalendarIntegrationService:
    """Service for Gmail/Outlook email and calendar integration."""

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
        self.integration_hub = IntegrationHubService(session)

        # Gmail API configuration
        self.gmail_base_url = "https://gmail.googleapis.com/gmail/v1"
        self.gmail_oauth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.gmail_token_url = "https://oauth2.googleapis.com/token"

        # Google Calendar API configuration
        self.calendar_base_url = "https://www.googleapis.com/calendar/v3"

        # Outlook API configuration
        self.outlook_base_url = "https://graph.microsoft.com/v1.0"
        self.outlook_oauth_url = (
            "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
        )
        self.outlook_token_url = (
            "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        )

        # Gmail scopes
        self.gmail_scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.metadata",
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/calendar.events.readonly",
        ]

        # Outlook scopes
        self.outlook_scopes = [
            "https://graph.microsoft.com/mail.read",
            "https://graph.microsoft.com/calendars.read",
            "https://graph.microsoft.com/user.read",
            "https://graph.microsoft.com/contacts.read",
        ]

        # Rate limits
        self.rate_limits = {
            "gmail": 1000,  # 1000 requests per 100 seconds
            "calendar": 1000,  # 1000 requests per 100 seconds
            "outlook": 10000,  # 10000 requests per 10 minutes
        }

    async def register_email_calendar_connector(self, service_type: str) -> str:
        """Register email/calendar connector in Integration Hub.

        Args:
            service_type: Either 'gmail' or 'outlook'

        Returns:
            Connector ID
        """
        try:
            if service_type == "gmail":
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
                        "max_emails": {
                            "type": "integer",
                            "default": 1000,
                            "description": "Maximum emails to sync per batch",
                        },
                        "include_attachments": {
                            "type": "boolean",
                            "default": false,
                            "description": "Whether to download email attachments",
                        },
                        "calendar_lookback_days": {
                            "type": "integer",
                            "default": 30,
                            "description": "Days to look back for calendar events",
                        },
                        "calendar_lookahead_days": {
                            "type": "integer",
                            "default": 90,
                            "description": "Days to look ahead for calendar events",
                        },
                    },
                    "required": ["client_id", "client_secret"],
                }

                name = "Gmail and Google Calendar Integration"
                scopes = self.gmail_scopes

            else:  # outlook
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
                            "description": "Microsoft tenant ID (optional for multi-tenant)",
                        },
                        "sync_frequency": {
                            "type": "string",
                            "enum": ["realtime", "hourly", "daily"],
                            "default": "hourly",
                        },
                        "max_emails": {
                            "type": "integer",
                            "default": 1000,
                            "description": "Maximum emails to sync per batch",
                        },
                        "include_attachments": {
                            "type": "boolean",
                            "default": false,
                            "description": "Whether to download email attachments",
                        },
                        "calendar_lookback_days": {
                            "type": "integer",
                            "default": 30,
                            "description": "Days to look back for calendar events",
                        },
                        "calendar_lookahead_days": {
                            "type": "integer",
                            "default": 90,
                            "description": "Days to look ahead for calendar events",
                        },
                    },
                    "required": ["client_id", "client_secret"],
                }

                name = "Outlook and Microsoft Calendar Integration"
                scopes = self.outlook_scopes

            connector = await self.integration_hub.register_connector(
                connector_type=service_type,
                name=name,
                version="1.0.0",
                developer="SingleBrief",
                capabilities=[
                    "read_emails",
                    "read_calendar",
                    "email_search",
                    "thread_tracking",
                    "contact_mapping",
                    "priority_scoring",
                    "calendar_analysis",
                ],
                config_schema=config_schema,
                description=f"Integration for {service_type.title()} email and calendar",
                required_scopes=scopes,
                supported_auth_types=["oauth2"],
                default_rate_limit_hour=self.rate_limits.get(service_type, 1000),
                default_rate_limit_day=self.rate_limits.get(service_type, 1000) * 24,
                burst_limit=50,
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
        """Initiate OAuth 2.0 flow for email/calendar access.

        Args:
            organization_id: Organization ID
            user_id: User ID
            service_type: 'gmail' or 'outlook'
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
            if service_type == "gmail":
                auth_params = {
                    "client_id": client_id,
                    "response_type": "code",
                    "scope": " ".join(self.gmail_scopes),
                    "redirect_uri": redirect_uri,
                    "state": state,
                    "access_type": "offline",
                    "prompt": "consent",
                }
                auth_url = f"{self.gmail_oauth_url}?{urlencode(auth_params)}"

            else:  # outlook
                auth_params = {
                    "client_id": client_id,
                    "response_type": "code",
                    "scope": " ".join(self.outlook_scopes),
                    "redirect_uri": redirect_uri,
                    "state": state,
                    "response_mode": "query",
                }
                auth_url = f"{self.outlook_oauth_url}?{urlencode(auth_params)}"

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
            service_type: 'gmail' or 'outlook'
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
            if service_type == "gmail":
                token_url = self.gmail_token_url
                token_data = {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": authorization_code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                }
            else:  # outlook
                token_url = self.outlook_token_url
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

    async def fetch_emails(
        self,
        integration_id: str,
        service_type: str,
        query: Optional[str] = None,
        max_results: int = 100,
        include_body: bool = True,
    ) -> List[Dict[str, Any]]:
        """Fetch emails from Gmail or Outlook.

        Args:
            integration_id: Integration ID
            service_type: 'gmail' or 'outlook'
            query: Search query
            max_results: Maximum emails to fetch
            include_body: Whether to include email body

        Returns:
            List of email dictionaries
        """
        session = self.session or await get_db_session().__anext__()

        try:
            # Get valid token
            token = await self._get_valid_token(session, integration_id)
            access_token = self._decrypt_token(token.access_token_encrypted)

            if service_type == "gmail":
                emails = await self._fetch_gmail_messages(
                    access_token, query, max_results, include_body
                )
            else:  # outlook
                emails = await self._fetch_outlook_messages(
                    access_token, query, max_results, include_body
                )

            # Log email fetch
            await self._log_operation(
                integration_id,
                None,
                "fetch_emails",
                f"Fetched {len(emails)} emails from {service_type}",
                {
                    "service_type": service_type,
                    "email_count": len(emails),
                    "query": query,
                },
            )

            return emails

        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            raise
        finally:
            if not self.session:
                await session.close()

    async def fetch_calendar_events(
        self,
        integration_id: str,
        service_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        calendar_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch calendar events from Google Calendar or Outlook Calendar.

        Args:
            integration_id: Integration ID
            service_type: 'gmail' or 'outlook'
            start_date: Start date for events
            end_date: End date for events
            calendar_id: Specific calendar ID (optional)

        Returns:
            List of calendar event dictionaries
        """
        session = self.session or await get_db_session().__anext__()

        try:
            # Get valid token
            token = await self._get_valid_token(session, integration_id)
            access_token = self._decrypt_token(token.access_token_encrypted)

            # Default date range
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if not end_date:
                end_date = datetime.now(timezone.utc) + timedelta(days=90)

            if service_type == "gmail":
                events = await self._fetch_google_calendar_events(
                    access_token, start_date, end_date, calendar_id
                )
            else:  # outlook
                events = await self._fetch_outlook_calendar_events(
                    access_token, start_date, end_date, calendar_id
                )

            # Log calendar fetch
            await self._log_operation(
                integration_id,
                None,
                "fetch_calendar",
                f"Fetched {len(events)} calendar events from {service_type}",
                {
                    "service_type": service_type,
                    "event_count": len(events),
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
            )

            return events

        except Exception as e:
            logger.error(f"Error fetching calendar events: {e}")
            raise
        finally:
            if not self.session:
                await session.close()

    async def analyze_email_threads(
        self, integration_id: str, service_type: str, thread_id: str
    ) -> Dict[str, Any]:
        """Analyze email thread for context and relationships.

        Args:
            integration_id: Integration ID
            service_type: 'gmail' or 'outlook'
            thread_id: Thread identifier

        Returns:
            Thread analysis results
        """
        session = self.session or await get_db_session().__anext__()

        try:
            # Get valid token
            token = await self._get_valid_token(session, integration_id)
            access_token = self._decrypt_token(token.access_token_encrypted)

            if service_type == "gmail":
                thread_data = await self._analyze_gmail_thread(access_token, thread_id)
            else:  # outlook
                thread_data = await self._analyze_outlook_conversation(
                    access_token, thread_id
                )

            # Analyze thread patterns
            analysis = {
                "thread_id": thread_id,
                "message_count": len(thread_data.get("messages", [])),
                "participants": self._extract_participants(thread_data),
                "date_range": self._get_thread_date_range(thread_data),
                "topics": self._extract_thread_topics(thread_data),
                "sentiment": self._analyze_thread_sentiment(thread_data),
                "action_items": self._extract_action_items(thread_data),
                "priority_score": self._calculate_thread_priority(thread_data),
            }

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing email thread: {e}")
            raise
        finally:
            if not self.session:
                await session.close()

    async def extract_contacts_and_relationships(
        self, integration_id: str, service_type: str
    ) -> List[Dict[str, Any]]:
        """Extract contact information and relationship mapping.

        Args:
            integration_id: Integration ID
            service_type: 'gmail' or 'outlook'

        Returns:
            List of contact relationships
        """
        session = self.session or await get_db_session().__anext__()

        try:
            # Get valid token
            token = await self._get_valid_token(session, integration_id)
            access_token = self._decrypt_token(token.access_token_encrypted)

            # Fetch recent emails to analyze contacts
            emails = await self.fetch_emails(
                integration_id, service_type, max_results=500, include_body=False
            )

            # Extract contact information
            contacts = {}
            for email in emails:
                # Process sender
                sender = email.get("from")
                if sender:
                    self._process_contact(contacts, sender, email, "sender")

                # Process recipients
                for recipient in email.get("to", []):
                    self._process_contact(contacts, recipient, email, "recipient")

                for recipient in email.get("cc", []):
                    self._process_contact(contacts, recipient, email, "cc")

            # Calculate relationship scores
            contact_list = []
            for email, contact_data in contacts.items():
                relationship_score = self._calculate_relationship_score(contact_data)
                contact_list.append(
                    {
                        "email": email,
                        "name": contact_data.get("name"),
                        "communication_frequency": contact_data.get("count", 0),
                        "last_contact": contact_data.get("last_contact"),
                        "relationship_score": relationship_score,
                        "interaction_types": contact_data.get("interaction_types", []),
                        "organization": self._extract_organization(email),
                    }
                )

            # Sort by relationship score
            contact_list.sort(key=lambda x: x["relationship_score"], reverse=True)

            return contact_list

        except Exception as e:
            logger.error(f"Error extracting contacts: {e}")
            raise
        finally:
            if not self.session:
                await session.close()

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
        # This would make a request to the token endpoint with the refresh token
        # and update the stored tokens
        raise NotImplementedError("Token refresh not yet implemented")

    async def _get_user_profile(
        self, access_token: str, service_type: str
    ) -> Dict[str, Any]:
        """Get user profile information from the service."""
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            if service_type == "gmail":
                url = f"{self.gmail_base_url}/users/me/profile"
            else:  # outlook
                url = f"{self.outlook_base_url}/me"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()

                        if service_type == "gmail":
                            return {
                                "id": data.get("emailAddress"),
                                "email": data.get("emailAddress"),
                                "username": data.get("emailAddress", "").split("@")[0],
                            }
                        else:  # outlook
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

    async def _fetch_gmail_messages(
        self,
        access_token: str,
        query: Optional[str],
        max_results: int,
        include_body: bool,
    ) -> List[Dict[str, Any]]:
        """Fetch messages from Gmail API."""
        headers = {"Authorization": f"Bearer {access_token}"}
        messages = []

        try:
            # First, get message IDs
            url = f"{self.gmail_base_url}/users/me/messages"
            params = {"maxResults": min(max_results, 500)}
            if query:
                params["q"] = query

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        message_ids = [msg["id"] for msg in data.get("messages", [])]

                        # Fetch detailed message data
                        for msg_id in message_ids[:max_results]:
                            msg_url = (
                                f"{self.gmail_base_url}/users/me/messages/{msg_id}"
                            )
                            msg_params = {
                                "format": "full" if include_body else "metadata"
                            }

                            async with session.get(
                                msg_url, headers=headers, params=msg_params
                            ) as msg_response:
                                if msg_response.status == 200:
                                    msg_data = await msg_response.json()
                                    processed_msg = self._process_gmail_message(
                                        msg_data, include_body
                                    )
                                    messages.append(processed_msg)

        except Exception as e:
            logger.error(f"Error fetching Gmail messages: {e}")

        return messages

    async def _fetch_outlook_messages(
        self,
        access_token: str,
        query: Optional[str],
        max_results: int,
        include_body: bool,
    ) -> List[Dict[str, Any]]:
        """Fetch messages from Outlook API."""
        headers = {"Authorization": f"Bearer {access_token}"}
        messages = []

        try:
            url = f"{self.outlook_base_url}/me/messages"
            params = {
                "$top": min(max_results, 1000),
                "$orderby": "receivedDateTime desc",
            }

            if query:
                params["$search"] = f'"{query}"'

            if include_body:
                params["$select"] = (
                    "id,subject,from,toRecipients,ccRecipients,receivedDateTime,body,importance,isRead"
                )
            else:
                params["$select"] = (
                    "id,subject,from,toRecipients,ccRecipients,receivedDateTime,importance,isRead"
                )

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        for msg_data in data.get("value", []):
                            processed_msg = self._process_outlook_message(
                                msg_data, include_body
                            )
                            messages.append(processed_msg)

        except Exception as e:
            logger.error(f"Error fetching Outlook messages: {e}")

        return messages

    async def _fetch_google_calendar_events(
        self,
        access_token: str,
        start_date: datetime,
        end_date: datetime,
        calendar_id: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Fetch events from Google Calendar."""
        headers = {"Authorization": f"Bearer {access_token}"}
        events = []

        try:
            cal_id = calendar_id or "primary"
            url = f"{self.calendar_base_url}/calendars/{cal_id}/events"
            params = {
                "timeMin": start_date.isoformat(),
                "timeMax": end_date.isoformat(),
                "singleEvents": "true",
                "orderBy": "startTime",
                "maxResults": 1000,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        for event_data in data.get("items", []):
                            processed_event = self._process_google_calendar_event(
                                event_data
                            )
                            events.append(processed_event)

        except Exception as e:
            logger.error(f"Error fetching Google Calendar events: {e}")

        return events

    async def _fetch_outlook_calendar_events(
        self,
        access_token: str,
        start_date: datetime,
        end_date: datetime,
        calendar_id: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Fetch events from Outlook Calendar."""
        headers = {"Authorization": f"Bearer {access_token}"}
        events = []

        try:
            if calendar_id:
                url = f"{self.outlook_base_url}/me/calendars/{calendar_id}/events"
            else:
                url = f"{self.outlook_base_url}/me/events"

            params = {
                "$filter": f"start/dateTime ge '{start_date.isoformat()}' and end/dateTime le '{end_date.isoformat()}'",
                "$orderby": "start/dateTime",
                "$top": 1000,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        for event_data in data.get("value", []):
                            processed_event = self._process_outlook_calendar_event(
                                event_data
                            )
                            events.append(processed_event)

        except Exception as e:
            logger.error(f"Error fetching Outlook Calendar events: {e}")

        return events

    def _process_gmail_message(
        self, msg_data: Dict[str, Any], include_body: bool
    ) -> Dict[str, Any]:
        """Process Gmail message data into standard format."""
        headers = {
            h["name"]: h["value"]
            for h in msg_data.get("payload", {}).get("headers", [])
        }

        # Extract body if requested
        body = ""
        if include_body:
            payload = msg_data.get("payload", {})
            body = self._extract_gmail_body(payload)

        return {
            "id": msg_data.get("id"),
            "thread_id": msg_data.get("threadId"),
            "subject": headers.get("Subject", ""),
            "from": headers.get("From", ""),
            "to": headers.get("To", "").split(",") if headers.get("To") else [],
            "cc": headers.get("Cc", "").split(",") if headers.get("Cc") else [],
            "date": headers.get("Date"),
            "body": body,
            "snippet": msg_data.get("snippet", ""),
            "labels": msg_data.get("labelIds", []),
            "is_read": "UNREAD" not in msg_data.get("labelIds", []),
            "service_type": "gmail",
        }

    def _process_outlook_message(
        self, msg_data: Dict[str, Any], include_body: bool
    ) -> Dict[str, Any]:
        """Process Outlook message data into standard format."""
        from_info = msg_data.get("from", {}).get("emailAddress", {})
        to_recipients = [
            r.get("emailAddress", {}).get("address", "")
            for r in msg_data.get("toRecipients", [])
        ]
        cc_recipients = [
            r.get("emailAddress", {}).get("address", "")
            for r in msg_data.get("ccRecipients", [])
        ]

        body = ""
        if include_body and msg_data.get("body"):
            body = msg_data["body"].get("content", "")

        return {
            "id": msg_data.get("id"),
            "thread_id": msg_data.get("conversationId"),
            "subject": msg_data.get("subject", ""),
            "from": from_info.get("address", ""),
            "to": to_recipients,
            "cc": cc_recipients,
            "date": msg_data.get("receivedDateTime"),
            "body": body,
            "snippet": body[:200] if body else "",
            "importance": msg_data.get("importance", "normal"),
            "is_read": msg_data.get("isRead", False),
            "service_type": "outlook",
        }

    def _process_google_calendar_event(
        self, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process Google Calendar event data."""
        start = event_data.get("start", {})
        end = event_data.get("end", {})

        return {
            "id": event_data.get("id"),
            "summary": event_data.get("summary", ""),
            "description": event_data.get("description", ""),
            "start_time": start.get("dateTime") or start.get("date"),
            "end_time": end.get("dateTime") or end.get("date"),
            "location": event_data.get("location"),
            "attendees": [a.get("email") for a in event_data.get("attendees", [])],
            "organizer": event_data.get("organizer", {}).get("email"),
            "status": event_data.get("status"),
            "created": event_data.get("created"),
            "updated": event_data.get("updated"),
            "service_type": "google_calendar",
        }

    def _process_outlook_calendar_event(
        self, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process Outlook Calendar event data."""
        start = event_data.get("start", {})
        end = event_data.get("end", {})

        return {
            "id": event_data.get("id"),
            "summary": event_data.get("subject", ""),
            "description": event_data.get("body", {}).get("content", ""),
            "start_time": start.get("dateTime"),
            "end_time": end.get("dateTime"),
            "location": event_data.get("location", {}).get("displayName"),
            "attendees": [
                a.get("emailAddress", {}).get("address")
                for a in event_data.get("attendees", [])
            ],
            "organizer": event_data.get("organizer", {})
            .get("emailAddress", {})
            .get("address"),
            "status": event_data.get("showAs"),
            "created": event_data.get("createdDateTime"),
            "updated": event_data.get("lastModifiedDateTime"),
            "service_type": "outlook_calendar",
        }

    def _extract_gmail_body(self, payload: Dict[str, Any]) -> str:
        """Extract text body from Gmail message payload."""
        # This is a simplified implementation
        # In practice, would need to handle multipart messages, HTML, etc.
        if payload.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode(
                "utf-8", errors="ignore"
            )

        # Check parts for text content
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get(
                "data"
            ):
                return base64.urlsafe_b64decode(part["body"]["data"]).decode(
                    "utf-8", errors="ignore"
                )

        return ""

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
            # Create email data source
            email_source = DataSource(
                integration_id=integration.id,
                source_type="email",
                external_id="primary",
                name=f"{service_type.title()} Email",
                description=f"Primary email account for {service_type}",
                source_metadata={
                    "email": oauth_token.external_email,
                    "service_type": service_type,
                },
                sync_frequency="hourly",
                privacy_level="sensitive",
            )
            session.add(email_source)

            # Create calendar data source
            calendar_source = DataSource(
                integration_id=integration.id,
                source_type="calendar",
                external_id="primary",
                name=f"{service_type.title()} Calendar",
                description=f"Primary calendar for {service_type}",
                source_metadata={
                    "email": oauth_token.external_email,
                    "service_type": service_type,
                },
                sync_frequency="hourly",
                privacy_level="standard",
            )
            session.add(calendar_source)

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

    # Analysis helper methods (simplified implementations)

    async def _analyze_gmail_thread(
        self, access_token: str, thread_id: str
    ) -> Dict[str, Any]:
        """Analyze Gmail thread."""
        # TODO: Implement thread analysis
        return {"messages": [], "thread_id": thread_id}

    async def _analyze_outlook_conversation(
        self, access_token: str, thread_id: str
    ) -> Dict[str, Any]:
        """Analyze Outlook conversation."""
        # TODO: Implement conversation analysis
        return {"messages": [], "conversation_id": thread_id}

    def _extract_participants(self, thread_data: Dict[str, Any]) -> List[str]:
        """Extract unique participants from thread."""
        # TODO: Implement participant extraction
        return []

    def _get_thread_date_range(self, thread_data: Dict[str, Any]) -> Dict[str, str]:
        """Get date range for thread."""
        # TODO: Implement date range calculation
        return {"start": "", "end": ""}

    def _extract_thread_topics(self, thread_data: Dict[str, Any]) -> List[str]:
        """Extract topics from thread."""
        # TODO: Implement topic extraction
        return []

    def _analyze_thread_sentiment(self, thread_data: Dict[str, Any]) -> str:
        """Analyze sentiment of thread."""
        # TODO: Implement sentiment analysis
        return "neutral"

    def _extract_action_items(self, thread_data: Dict[str, Any]) -> List[str]:
        """Extract action items from thread."""
        # TODO: Implement action item extraction
        return []

    def _calculate_thread_priority(self, thread_data: Dict[str, Any]) -> float:
        """Calculate priority score for thread."""
        # TODO: Implement priority scoring
        return 0.5

    def _process_contact(
        self,
        contacts: Dict[str, Any],
        contact_info: str,
        email: Dict[str, Any],
        interaction_type: str,
    ) -> None:
        """Process contact information."""
        # TODO: Implement contact processing
        pass

    def _calculate_relationship_score(self, contact_data: Dict[str, Any]) -> float:
        """Calculate relationship strength score."""
        # TODO: Implement relationship scoring
        return 0.5

    def _extract_organization(self, email: str) -> Optional[str]:
        """Extract organization from email address."""
        if "@" in email:
            domain = email.split("@")[1]
            return domain.split(".")[0].title()
        return None

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

# Singleton instances
email_calendar_service = EmailCalendarIntegrationService()
