"""Tests for Slack Integration Service and API endpoints."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.slack_integration import SlackIntegrationService
from app.models.integration import Integration, OAuthToken, DataSource
from app.models.user import User, Organization


class TestSlackIntegrationService:
    """Test cases for SlackIntegrationService."""
    
    @pytest.fixture
    async def slack_service(self):
        """Create a SlackIntegrationService instance for testing."""
        return SlackIntegrationService()
    
    @pytest.fixture
    async def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock(spec=AsyncSession)
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.close = AsyncMock()
        session.refresh = AsyncMock()
        session.add = MagicMock()
        session.execute = AsyncMock()
        return session
    
    @pytest.fixture
    def sample_integration(self):
        """Create a sample integration for testing."""
        return Integration(
            id="test-integration-id",
            organization_id="test-org-id",
            configured_by_user_id="test-user-id",
            service_type="slack",
            service_name="Slack Workspace",
            integration_key="slack-test-org-id",
            config={
                "client_id": "test-client-id",
                "client_secret": "test-client-secret",
                "signing_secret": "test-signing-secret"
            },
            capabilities=["read_messages", "read_channels"],
            scopes=["channels:read", "channels:history"],
            status="active"
        )
    
    @pytest.fixture
    def sample_oauth_token(self):
        """Create a sample OAuth token for testing."""
        return OAuthToken(
            id="test-token-id",
            integration_id="test-integration-id",
            user_id="test-user-id",
            access_token_encrypted="encrypted-access-token",
            token_type="Bearer",
            scopes=["channels:read", "channels:history"],
            external_user_id="U1234567890",
            external_username="testuser",
            status="active",
            encryption_key_id="default",
            encryption_algorithm="AES-256-GCM"
        )
    
    async def test_register_slack_connector(self, slack_service, mock_session):
        """Test registering the Slack connector."""
        # Mock the integration hub service
        with patch.object(slack_service, 'integration_hub') as mock_hub:
            mock_connector = MagicMock()
            mock_connector.id = "test-connector-id"
            mock_hub.register_connector.return_value = mock_connector
            
            connector_id = await slack_service.register_slack_connector()
            
            assert connector_id == "test-connector-id"
            mock_hub.register_connector.assert_called_once()
            
            # Verify connector registration parameters
            call_args = mock_hub.register_connector.call_args
            assert call_args[1]["connector_type"] == "slack"
            assert call_args[1]["name"] == "Slack Workspace Integration"
            assert "read_messages" in call_args[1]["capabilities"]
    
    async def test_initiate_oauth_flow(self, slack_service, mock_session, sample_integration):
        """Test initiating OAuth flow."""
        # Mock database query result
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_integration
        mock_session.execute.return_value = mock_result
        
        slack_service.session = mock_session
        
        auth_url = await slack_service.initiate_oauth_flow(
            organization_id="test-org-id",
            user_id="test-user-id",
            redirect_uri="http://localhost:3000/callback"
        )
        
        assert "slack.com/oauth/v2/authorize" in auth_url
        assert "client_id=test-client-id" in auth_url
        assert "redirect_uri=" in auth_url
        assert "scope=" in auth_url
    
    @patch('aiohttp.ClientSession.post')
    async def test_complete_oauth_flow(self, mock_post, slack_service, mock_session, sample_integration):
        """Test completing OAuth flow."""
        # Mock database query result
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_integration
        mock_session.execute.return_value = mock_result
        
        # Mock HTTP response from Slack
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "ok": True,
            "access_token": "xoxb-test-token",
            "token_type": "Bearer",
            "scope": "channels:read,channels:history",
            "team": {
                "id": "T1234567890",
                "name": "Test Team",
                "domain": "test-team"
            },
            "authed_user": {
                "id": "U1234567890",
                "username": "testuser",
                "email": "test@example.com"
            }
        }
        mock_post.return_value.__aenter__.return_value = mock_response
        
        slack_service.session = mock_session
        
        # Mock token encryption
        with patch.object(slack_service, '_encrypt_token', return_value="encrypted-token"):
            with patch.object(slack_service, '_initialize_data_sources'):
                oauth_token = await slack_service.complete_oauth_flow(
                    organization_id="test-org-id",
                    user_id="test-user-id",
                    authorization_code="test-auth-code",
                    redirect_uri="http://localhost:3000/callback"
                )
        
        assert oauth_token.external_user_id == "U1234567890"
        assert oauth_token.external_username == "testuser"
        assert oauth_token.token_type == "Bearer"
        mock_session.add.assert_called()
        mock_session.commit.assert_called()
    
    @patch('aiohttp.ClientSession.post')
    async def test_fetch_channels(self, mock_post, slack_service, mock_session, sample_oauth_token):
        """Test fetching Slack channels."""
        # Mock getting valid token
        mock_token_result = AsyncMock()
        mock_token_result.scalar_one_or_none.return_value = sample_oauth_token
        mock_session.execute.return_value = mock_token_result
        
        # Mock HTTP response from Slack
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "ok": True,
            "channels": [
                {
                    "id": "C1234567890",
                    "name": "general",
                    "is_private": False,
                    "is_archived": False,
                    "num_members": 10,
                    "purpose": {"value": "General discussion"},
                    "topic": {"value": "Company updates"}
                },
                {
                    "id": "C0987654321",
                    "name": "random",
                    "is_private": False,
                    "is_archived": False,
                    "num_members": 5,
                    "purpose": {"value": "Random stuff"},
                    "topic": {"value": ""}
                }
            ]
        }
        mock_post.return_value.__aenter__.return_value = mock_response
        
        slack_service.session = mock_session
        
        # Mock token decryption
        with patch.object(slack_service, '_decrypt_token', return_value="decrypted-token"):
            channels = await slack_service.fetch_channels("test-integration-id")
        
        assert len(channels) == 2
        assert channels[0]["name"] == "general"
        assert channels[1]["name"] == "random"
        assert channels[0]["is_private"] is False
    
    @patch('aiohttp.ClientSession.post')
    async def test_fetch_messages(self, mock_post, slack_service, mock_session, sample_oauth_token):
        """Test fetching messages from a channel."""
        # Mock getting valid token
        mock_token_result = AsyncMock()
        mock_token_result.scalar_one_or_none.return_value = sample_oauth_token
        mock_session.execute.return_value = mock_token_result
        
        # Mock HTTP response from Slack
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "ok": True,
            "messages": [
                {
                    "type": "message",
                    "user": "U1234567890",
                    "text": "Hello world!",
                    "ts": "1234567890.123456"
                },
                {
                    "type": "message",
                    "user": "U0987654321",
                    "text": "How's everyone doing?",
                    "ts": "1234567891.123456"
                }
            ]
        }
        mock_post.return_value.__aenter__.return_value = mock_response
        
        slack_service.session = mock_session
        
        # Mock token decryption
        with patch.object(slack_service, '_decrypt_token', return_value="decrypted-token"):
            messages = await slack_service.fetch_messages(
                integration_id="test-integration-id",
                channel_id="C1234567890",
                limit=100
            )
        
        assert len(messages) == 2
        assert messages[0]["text"] == "Hello world!"
        assert messages[1]["text"] == "How's everyone doing?"
        assert messages[0]["user"] == "U1234567890"
    
    @patch('aiohttp.ClientSession.post')
    async def test_search_messages(self, mock_post, slack_service, mock_session, sample_oauth_token):
        """Test searching messages."""
        # Mock getting valid token
        mock_token_result = AsyncMock()
        mock_token_result.scalar_one_or_none.return_value = sample_oauth_token
        mock_session.execute.return_value = mock_token_result
        
        # Mock HTTP response from Slack
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "ok": True,
            "messages": {
                "total": 1,
                "matches": [
                    {
                        "type": "message",
                        "user": "U1234567890",
                        "text": "Project update meeting tomorrow",
                        "ts": "1234567890.123456",
                        "channel": {"id": "C1234567890", "name": "general"}
                    }
                ]
            }
        }
        mock_post.return_value.__aenter__.return_value = mock_response
        
        slack_service.session = mock_session
        
        # Mock token decryption
        with patch.object(slack_service, '_decrypt_token', return_value="decrypted-token"):
            results = await slack_service.search_messages(
                integration_id="test-integration-id",
                query="project update"
            )
        
        assert results["total"] == 1
        assert len(results["matches"]) == 1
        assert "project update" in results["matches"][0]["text"].lower()
    
    async def test_setup_real_time_events(self, slack_service, mock_session, sample_integration):
        """Test setting up real-time events."""
        # Mock database query result
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_integration
        mock_session.execute.return_value = mock_result
        
        slack_service.session = mock_session
        
        event_config = await slack_service.setup_real_time_events(
            integration_id="test-integration-id",
            event_url="https://example.com/webhooks/slack"
        )
        
        assert event_config["webhook_url"] == "https://example.com/webhooks/slack"
        assert "message.channels" in event_config["event_types"]
        assert "reaction_added" in event_config["event_types"]
        mock_session.commit.assert_called()
    
    async def test_process_webhook_event_url_verification(self, slack_service):
        """Test processing URL verification webhook event."""
        event_data = {
            "type": "url_verification",
            "challenge": "test-challenge-token"
        }
        
        with patch.object(slack_service, '_verify_webhook_signature', return_value=True):
            result = await slack_service.process_webhook_event(
                integration_id="test-integration-id",
                event_data=event_data,
                headers={}
            )
        
        assert result == {"challenge": "test-challenge-token"}
    
    async def test_process_webhook_event_message(self, slack_service, mock_session):
        """Test processing message webhook event."""
        event_data = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "user": "U1234567890",
                "text": "Hello from webhook!",
                "channel": "C1234567890",
                "ts": "1234567890.123456"
            }
        }
        
        slack_service.session = mock_session
        
        with patch.object(slack_service, '_verify_webhook_signature', return_value=True):
            with patch.object(slack_service, '_process_message_event') as mock_process:
                result = await slack_service.process_webhook_event(
                    integration_id="test-integration-id",
                    event_data=event_data,
                    headers={}
                )
        
        assert result is True
        mock_process.assert_called_once()


class TestSlackAPI:
    """Test cases for Slack API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the API."""
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)
    
    @pytest.fixture
    def mock_current_user(self):
        """Mock current user dependency."""
        return User(
            id="test-user-id",
            email="test@example.com",
            username="testuser"
        )
    
    @pytest.fixture
    def mock_current_org(self):
        """Mock current organization dependency."""
        return Organization(
            id="test-org-id",
            name="Test Organization"
        )
    
    async def test_setup_slack_integration(self, client, mock_current_user, mock_current_org):
        """Test setting up Slack integration via API."""
        with patch('app.api.v1.endpoints.slack.get_current_user', return_value=mock_current_user):
            with patch('app.api.v1.endpoints.slack.get_current_organization', return_value=mock_current_org):
                with patch('app.api.v1.endpoints.slack.get_db_session'):
                    with patch('app.api.v1.endpoints.slack.slack_integration_service.register_slack_connector'):
                        response = client.post("/api/v1/integrations/slack/setup", json={
                            "client_id": "test-client-id",
                            "client_secret": "test-client-secret",
                            "signing_secret": "test-signing-secret",
                            "channels": ["general", "random"],
                            "keywords": ["urgent", "important"],
                            "sync_frequency": "realtime"
                        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "configured"
    
    async def test_initiate_oauth(self, client, mock_current_user, mock_current_org):
        """Test initiating OAuth flow via API."""
        with patch('app.api.v1.endpoints.slack.get_current_user', return_value=mock_current_user):
            with patch('app.api.v1.endpoints.slack.get_current_organization', return_value=mock_current_org):
                with patch('app.api.v1.endpoints.slack.get_db_session'):
                    with patch('app.api.v1.endpoints.slack.slack_integration_service.initiate_oauth_flow') as mock_oauth:
                        mock_oauth.return_value = "https://slack.com/oauth/v2/authorize?client_id=test&state=test-state"
                        
                        response = client.post("/api/v1/integrations/slack/oauth/initiate", json={
                            "redirect_uri": "http://localhost:3000/callback"
                        })
        
        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "slack.com/oauth/v2/authorize" in data["authorization_url"]
    
    async def test_complete_oauth(self, client, mock_current_user, mock_current_org):
        """Test completing OAuth flow via API."""
        mock_token = OAuthToken(
            id="test-token-id",
            integration_id="test-integration-id",
            external_username="testuser"
        )
        
        with patch('app.api.v1.endpoints.slack.get_current_user', return_value=mock_current_user):
            with patch('app.api.v1.endpoints.slack.get_current_organization', return_value=mock_current_org):
                with patch('app.api.v1.endpoints.slack.get_db_session'):
                    with patch('app.api.v1.endpoints.slack.slack_integration_service.complete_oauth_flow') as mock_complete:
                        mock_complete.return_value = mock_token
                        
                        # Mock integration query
                        with patch('sqlalchemy.ext.asyncio.AsyncSession.execute') as mock_execute:
                            mock_result = AsyncMock()
                            mock_integration = Integration(
                                id="test-integration-id",
                                integration_metadata={"team_name": "Test Team"}
                            )
                            mock_result.scalar_one.return_value = mock_integration
                            mock_execute.return_value = mock_result
                            
                            response = client.post("/api/v1/integrations/slack/oauth/complete", json={
                                "code": "test-auth-code",
                                "redirect_uri": "http://localhost:3000/callback"
                            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["team_name"] == "Test Team"
        assert data["user_name"] == "testuser"
    
    async def test_get_channels(self, client, mock_current_user, mock_current_org):
        """Test getting Slack channels via API."""
        mock_channels = [
            {
                "id": "C1234567890",
                "name": "general",
                "is_private": False,
                "is_archived": False,
                "num_members": 10,
                "purpose": {"value": "General discussion"},
                "topic": {"value": "Company updates"}
            }
        ]
        
        with patch('app.api.v1.endpoints.slack.get_current_user', return_value=mock_current_user):
            with patch('app.api.v1.endpoints.slack.get_current_organization', return_value=mock_current_org):
                with patch('app.api.v1.endpoints.slack.get_db_session'):
                    # Mock integration query
                    with patch('sqlalchemy.ext.asyncio.AsyncSession.execute') as mock_execute:
                        mock_result = AsyncMock()
                        mock_integration = Integration(id="test-integration-id", status="active")
                        mock_result.scalar_one_or_none.return_value = mock_integration
                        mock_execute.return_value = mock_result
                        
                        with patch('app.api.v1.endpoints.slack.slack_integration_service.fetch_channels') as mock_fetch:
                            mock_fetch.return_value = mock_channels
                            
                            response = client.get("/api/v1/integrations/slack/channels")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "general"
        assert data[0]["is_private"] is False
    
    async def test_webhook_url_verification(self, client):
        """Test webhook URL verification challenge."""
        challenge_data = {
            "type": "url_verification",
            "challenge": "test-challenge-token"
        }
        
        response = client.post("/api/v1/integrations/slack/webhooks/events", json=challenge_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["challenge"] == "test-challenge-token"


if __name__ == "__main__":
    pytest.main([__file__])