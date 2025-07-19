"""
Authentication endpoints
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import structlog

from app.core.database import get_db_session, get_redis
from app.core.security import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    create_email_verification_token, verify_email_verification_token,
    generate_password_reset_token
)
from app.models.user import User, Organization, UserRole
from app.models.auth import RefreshToken, PasswordResetToken, EmailVerificationToken, LoginAttempt
from app.schemas.auth import (
    UserRegister, UserLogin, TokenResponse, Token, RefreshTokenRequest,
    PasswordReset, PasswordChange, EmailVerification, ResendVerification,
    OAuthLogin
)
from app.schemas.user import UserResponse, OrganizationResponse
from app.auth.dependencies import (
    get_current_user, get_current_active_user, verify_refresh_token,
    log_login_attempt, get_client_ip, get_user_agent
)
from app.auth.oauth import get_oauth_provider, extract_user_data_from_oauth

logger = structlog.get_logger(__name__)
router = APIRouter()
security = HTTPBearer()


async def send_verification_email(email: str, token: str):
    """Send email verification email (background task)"""
    # TODO: Implement email sending
    logger.info("Email verification sent", email=email, token=token[:10] + "...")


async def send_password_reset_email(email: str, token: str):
    """Send password reset email (background task)"""
    # TODO: Implement email sending  
    logger.info("Password reset email sent", email=email, token=token[:10] + "...")


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """Register a new user"""
    try:
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == user_data.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        password_hash = hash_password(user_data.password)
        
        # Create or find organization
        organization = None
        if user_data.organization_name:
            # Create new organization
            org_slug = user_data.organization_name.lower().replace(" ", "-")
            organization = Organization(
                name=user_data.organization_name,
                slug=org_slug
            )
            db.add(organization)
            await db.flush()  # Get the ID
        
        # Create user
        user = User(
            email=user_data.email,
            password_hash=password_hash,
            full_name=user_data.full_name,
            role=UserRole.ADMIN if organization else UserRole.TEAM_MEMBER,
            organization_id=organization.id if organization else None,
            is_active=True,
            is_verified=False  # Require email verification
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Create email verification token
        verification_token = create_email_verification_token(user.email)
        email_token = EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_password(verification_token),
            email=user.email,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.add(email_token)
        await db.commit()
        
        # Send verification email
        background_tasks.add_task(send_verification_email, user.email, verification_token)
        
        # Create tokens for immediate login
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role,
                "organization_id": str(organization.id) if organization else None
            }
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Store refresh token
        refresh_token_record = RefreshToken(
            user_id=user.id,
            token_hash=hash_password(refresh_token),
            jti=str(uuid.uuid4()),
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.add(refresh_token_record)
        await db.commit()
        
        # Log successful registration
        await log_login_attempt(
            email=user.email,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            success=True,
            user_id=str(user.id),
            db=db
        )
        
        return TokenResponse(
            user=UserResponse.from_orm(user),
            tokens=Token(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=1800  # 30 minutes
            ),
            organization=OrganizationResponse.from_orm(organization) if organization else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registration failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    user_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """Login user with email and password"""
    try:
        # Get user
        result = await db.execute(select(User).where(User.email == user_data.email))
        user = result.scalar_one_or_none()
        
        if not user:
            await log_login_attempt(
                email=user_data.email,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                success=False,
                failure_reason="User not found",
                db=db
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check password
        if not verify_password(user_data.password, user.password_hash):
            # Increment failed attempts
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            
            await db.commit()
            
            await log_login_attempt(
                email=user_data.email,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                success=False,
                failure_reason="Invalid password",
                user_id=str(user.id),
                db=db
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if user is locked
        if user.is_locked:
            await log_login_attempt(
                email=user_data.email,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                success=False,
                failure_reason="Account locked",
                user_id=str(user.id),
                db=db
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is locked"
            )
        
        # Check if user is active
        if not user.is_active:
            await log_login_attempt(
                email=user_data.email,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                success=False,
                failure_reason="Account inactive",
                user_id=str(user.id),
                db=db
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )
        
        # Reset failed attempts and update last login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        user.login_count += 1
        
        # Create tokens
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role,
                "organization_id": str(user.organization_id) if user.organization_id else None
            }
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Store refresh token
        refresh_token_record = RefreshToken(
            user_id=user.id,
            token_hash=hash_password(refresh_token),
            jti=str(uuid.uuid4()),
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.add(refresh_token_record)
        await db.commit()
        
        # Log successful login
        await log_login_attempt(
            email=user.email,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            success=True,
            user_id=str(user.id),
            db=db
        )
        
        return TokenResponse(
            user=UserResponse.from_orm(user),
            tokens=Token(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=1800  # 30 minutes
            ),
            organization=OrganizationResponse.from_orm(user.organization) if user.organization else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Refresh access token using refresh token"""
    try:
        user = await verify_refresh_token(token_data.refresh_token, db)
        
        # Create new access token
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role,
                "organization_id": str(user.organization_id) if user.organization_id else None
            }
        )
        
        return Token(
            access_token=access_token,
            refresh_token=token_data.refresh_token,  # Keep same refresh token
            expires_in=1800
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token"
        )


@router.post("/logout")
async def logout_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Logout user and revoke refresh tokens"""
    try:
        # Revoke all refresh tokens for user
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == current_user.id)
            .values(is_revoked=True, revoked_at=datetime.utcnow())
        )
        await db.commit()
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error("Logout failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/verify-email")
async def verify_email(
    verification: EmailVerification,
    db: AsyncSession = Depends(get_db_session)
):
    """Verify user email address"""
    try:
        # Verify token
        email = verify_email_verification_token(verification.token)
        
        # Find verification token in database
        token_hash = hash_password(verification.token)
        result = await db.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.token_hash == token_hash,
                EmailVerificationToken.is_used == False
            )
        )
        db_token = result.scalar_one_or_none()
        
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        # Mark token as used
        db_token.is_used = True
        db_token.used_at = datetime.utcnow()
        
        # Mark user as verified
        user_result = await db.execute(
            select(User).where(User.id == db_token.user_id)
        )
        user = user_result.scalar_one()
        user.is_verified = True
        
        await db.commit()
        
        return {"message": "Email verified successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Email verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email verification failed"
        )


@router.post("/resend-verification")
async def resend_verification_email(
    request_data: ResendVerification,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """Resend email verification"""
    try:
        # Find user
        result = await db.execute(select(User).where(User.email == request_data.email))
        user = result.scalar_one_or_none()
        
        if not user:
            # Don't reveal if email exists
            return {"message": "If the email exists, verification email will be sent"}
        
        if user.is_verified:
            return {"message": "Email is already verified"}
        
        # Create new verification token
        verification_token = create_email_verification_token(user.email)
        email_token = EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_password(verification_token),
            email=user.email,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.add(email_token)
        await db.commit()
        
        # Send verification email
        background_tasks.add_task(send_verification_email, user.email, verification_token)
        
        return {"message": "Verification email sent"}
        
    except Exception as e:
        logger.error("Resend verification failed", error=str(e))
        return {"message": "If the email exists, verification email will be sent"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return UserResponse.from_orm(current_user)


@router.get("/oauth/{provider}/url")
async def get_oauth_url(
    provider: str,
    redirect_uri: str,
    state: str = None
):
    """Get OAuth authorization URL"""
    try:
        oauth_provider = await get_oauth_provider(provider)
        auth_url = await oauth_provider.get_authorization_url(redirect_uri, state)
        
        return {"auth_url": auth_url, "state": state}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("OAuth URL generation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate OAuth URL"
        )


@router.post("/oauth/{provider}/callback", response_model=TokenResponse)
async def oauth_callback(
    provider: str,
    oauth_data: OAuthLogin,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """Handle OAuth callback and login/register user"""
    try:
        oauth_provider = await get_oauth_provider(provider)
        
        # Exchange code for tokens
        token_response = await oauth_provider.exchange_code(
            oauth_data.code, 
            oauth_data.redirect_uri
        )
        
        # Get user info
        user_info = await oauth_provider.get_user_info(
            token_response["access_token"]
        )
        
        # Extract user data
        user_data = extract_user_data_from_oauth(provider, user_info)
        
        # Find or create user
        result = await db.execute(select(User).where(User.email == user_data["email"]))
        user = result.scalar_one_or_none()
        
        if not user:
            # Create new user
            user = User(
                email=user_data["email"],
                full_name=user_data["full_name"],
                avatar_url=user_data["avatar_url"],
                role=UserRole.TEAM_MEMBER,
                is_active=True,
                is_verified=user_data["is_verified"]
            )
            
            # Set provider ID
            if provider == "google":
                user.google_id = user_data["provider_id"]
            elif provider == "microsoft":
                user.microsoft_id = user_data["provider_id"]
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            # Update provider ID if not set
            if provider == "google" and not user.google_id:
                user.google_id = user_data["provider_id"]
            elif provider == "microsoft" and not user.microsoft_id:
                user.microsoft_id = user_data["provider_id"]
            
            # Update last login
            user.last_login = datetime.utcnow()
            user.login_count += 1
            await db.commit()
        
        # Create tokens
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role,
                "organization_id": str(user.organization_id) if user.organization_id else None
            }
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Store refresh token
        refresh_token_record = RefreshToken(
            user_id=user.id,
            token_hash=hash_password(refresh_token),
            jti=str(uuid.uuid4()),
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.add(refresh_token_record)
        await db.commit()
        
        # Log successful login
        await log_login_attempt(
            email=user.email,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            success=True,
            user_id=str(user.id),
            db=db
        )
        
        return TokenResponse(
            user=UserResponse.from_orm(user),
            tokens=Token(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=1800
            ),
            organization=OrganizationResponse.from_orm(user.organization) if user.organization else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("OAuth callback failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth authentication failed"
        )