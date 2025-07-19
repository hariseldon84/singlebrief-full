"""
OAuth 2.0 integration for Google and Microsoft
"""

import secrets
from typing import Optional, Dict, Any
import httpx
from fastapi import HTTPException, status
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class OAuthProvider:
    """Base OAuth provider class"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
    
    async def get_authorization_url(self, redirect_uri: str, state: str = None) -> str:
        """Get OAuth authorization URL"""
        raise NotImplementedError
    
    async def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        raise NotImplementedError
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from OAuth provider"""
        raise NotImplementedError


class GoogleOAuth(OAuthProvider):
    """Google OAuth 2.0 provider"""
    
    def __init__(self):
        super().__init__(
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET
        )
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        self.scopes = [
            "openid",
            "email", 
            "profile",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/calendar.readonly"
        ]
    
    async def get_authorization_url(self, redirect_uri: str, state: str = None) -> str:
        """Get Google OAuth authorization URL"""
        if not state:
            state = secrets.token_urlsafe(32)
        
        scope = " ".join(self.scopes)
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "response_type": "code",
            "state": state,
            "access_type": "offline",  # For refresh tokens
            "prompt": "consent"  # Force consent for refresh token
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.auth_url}?{query_string}"
    
    async def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange Google authorization code for tokens"""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.token_url, data=data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error("Google token exchange failed", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange authorization code"
                )
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get Google user information"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.user_info_url, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error("Google user info request failed", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user information"
                )
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh Google access token"""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.token_url, data=data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error("Google token refresh failed", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to refresh token"
                )


class MicrosoftOAuth(OAuthProvider):
    """Microsoft OAuth 2.0 provider"""
    
    def __init__(self):
        super().__init__(
            client_id=settings.MICROSOFT_CLIENT_ID,
            client_secret=settings.MICROSOFT_CLIENT_SECRET
        )
        self.tenant = "common"  # Use common for multi-tenant
        self.auth_url = f"https://login.microsoftonline.com/{self.tenant}/oauth2/v2.0/authorize"
        self.token_url = f"https://login.microsoftonline.com/{self.tenant}/oauth2/v2.0/token"
        self.user_info_url = "https://graph.microsoft.com/v1.0/me"
        self.scopes = [
            "openid",
            "email",
            "profile",
            "offline_access",  # For refresh tokens
            "https://graph.microsoft.com/Mail.Read",
            "https://graph.microsoft.com/Calendars.Read"
        ]
    
    async def get_authorization_url(self, redirect_uri: str, state: str = None) -> str:
        """Get Microsoft OAuth authorization URL"""
        if not state:
            state = secrets.token_urlsafe(32)
        
        scope = " ".join(self.scopes)
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "response_type": "code",
            "state": state,
            "response_mode": "query"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.auth_url}?{query_string}"
    
    async def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange Microsoft authorization code for tokens"""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "scope": " ".join(self.scopes)
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.token_url, data=data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error("Microsoft token exchange failed", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange authorization code"
                )
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get Microsoft user information"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.user_info_url, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error("Microsoft user info request failed", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user information"
                )
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh Microsoft access token"""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "scope": " ".join(self.scopes)
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.token_url, data=data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error("Microsoft token refresh failed", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to refresh token"
                )


# OAuth provider instances
google_oauth = GoogleOAuth()
microsoft_oauth = MicrosoftOAuth()


async def get_oauth_provider(provider: str) -> OAuthProvider:
    """Get OAuth provider by name"""
    providers = {
        "google": google_oauth,
        "microsoft": microsoft_oauth
    }
    
    if provider not in providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}"
        )
    
    return providers[provider]


def extract_user_data_from_oauth(provider: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
    """Extract standardized user data from OAuth provider response"""
    if provider == "google":
        return {
            "email": user_info.get("email"),
            "full_name": user_info.get("name"),
            "avatar_url": user_info.get("picture"),
            "provider_id": user_info.get("id"),
            "is_verified": user_info.get("verified_email", False)
        }
    elif provider == "microsoft":
        return {
            "email": user_info.get("mail") or user_info.get("userPrincipalName"),
            "full_name": user_info.get("displayName"),
            "avatar_url": None,  # Microsoft Graph doesn't return avatar in basic profile
            "provider_id": user_info.get("id"),
            "is_verified": True  # Microsoft accounts are pre-verified
        }
    
    raise ValueError(f"Unknown provider: {provider}")


class OAuthTokenManager:
    """Manage OAuth tokens for external services"""
    
    @staticmethod
    async def store_oauth_tokens(
        user_id: str,
        provider: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_in: Optional[int] = None
    ):
        """Store OAuth tokens for a user"""
        # TODO: Implement secure token storage
        # This would typically encrypt tokens and store in database
        pass
    
    @staticmethod
    async def get_oauth_tokens(user_id: str, provider: str) -> Optional[Dict[str, Any]]:
        """Get stored OAuth tokens for a user"""
        # TODO: Implement token retrieval
        pass
    
    @staticmethod
    async def refresh_oauth_tokens(user_id: str, provider: str) -> Optional[Dict[str, Any]]:
        """Refresh OAuth tokens for a user"""
        # TODO: Implement token refresh
        pass