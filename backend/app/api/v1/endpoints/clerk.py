"""
Clerk integration endpoints for user and organization sync
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.models.user import User
from app.models.user import Organization
from app.auth.dependencies import get_current_user
from clerk_backend_sdk import Client

logger = structlog.get_logger(__name__)
router = APIRouter()

# Initialize Clerk client
from app.core.config import settings
clerk_client = Client()

class ClerkUserSync(BaseModel):
    clerk_user_id: str
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None

class ClerkOrganizationSync(BaseModel):
    clerk_org_id: str
    name: str
    slug: Optional[str] = None
    image_url: Optional[str] = None
    members_count: Optional[int] = None
    created_at: Optional[str] = None

async def verify_clerk_token(authorization: str = Header(None)) -> str:
    """Verify Clerk JWT token"""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace('Bearer ', '')
    
    # TODO: Implement proper Clerk JWT verification
    # For now, we'll just extract the token
    # In production, verify with Clerk's public key
    
    return token

@router.post("/sync-user")
async def sync_user(
    user_data: ClerkUserSync,
    db: Session = Depends(get_db),
    token: str = Depends(verify_clerk_token)
):
    """Sync user data from Clerk to local database"""
    try:
        # Check if user already exists
        user = db.query(User).filter(User.clerk_user_id == user_data.clerk_user_id).first()
        
        if not user:
            # Create new user
            user = User(
                clerk_user_id=user_data.clerk_user_id,
                email=user_data.email,
                full_name=user_data.full_name,
                avatar_url=user_data.avatar_url,
                phone=user_data.phone,
                is_active=True,
                email_verified=True,  # Clerk handles verification
            )
            db.add(user)
        else:
            # Update existing user
            user.email = user_data.email
            user.full_name = user_data.full_name
            user.avatar_url = user_data.avatar_url
            user.phone = user_data.phone
        
        db.commit()
        db.refresh(user)
        
        logger.info("User synced successfully", user_id=user.id, clerk_id=user_data.clerk_user_id)
        
        return {
            "success": True,
            "user_id": user.id,
            "message": "User synced successfully"
        }
        
    except Exception as e:
        logger.error("Failed to sync user", error=str(e), clerk_id=user_data.clerk_user_id)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync user data"
        )

@router.post("/sync-organization")
async def sync_organization(
    org_data: ClerkOrganizationSync,
    db: Session = Depends(get_db),
    token: str = Depends(verify_clerk_token)
):
    """Sync organization data from Clerk to local database"""
    try:
        # Check if organization already exists
        org = db.query(Organization).filter(Organization.clerk_org_id == org_data.clerk_org_id).first()
        
        if not org:
            # Create new organization
            org = Organization(
                clerk_org_id=org_data.clerk_org_id,
                name=org_data.name,
                slug=org_data.slug,
                logo_url=org_data.image_url,
                is_active=True,
            )
            db.add(org)
        else:
            # Update existing organization
            org.name = org_data.name
            org.slug = org_data.slug
            org.logo_url = org_data.image_url
        
        db.commit()
        db.refresh(org)
        
        logger.info("Organization synced successfully", org_id=org.id, clerk_id=org_data.clerk_org_id)
        
        return {
            "success": True,
            "organization_id": org.id,
            "message": "Organization synced successfully"
        }
        
    except Exception as e:
        logger.error("Failed to sync organization", error=str(e), clerk_id=org_data.clerk_org_id)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync organization data"
        )

@router.post("/webhook")
async def clerk_webhook(
    payload: Dict[str, Any],
    svix_id: str = Header(None),
    svix_timestamp: str = Header(None),
    svix_signature: str = Header(None),
    db: Session = Depends(get_db)
):
    """Handle Clerk webhooks for real-time sync"""
    try:
        # TODO: Verify webhook signature with Svix
        
        event_type = payload.get("type")
        data = payload.get("data", {})
        
        if event_type == "user.created":
            # Handle new user creation
            user_data = ClerkUserSync(
                clerk_user_id=data["id"],
                email=data["email_addresses"][0]["email_address"],
                full_name=f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
                avatar_url=data.get("image_url"),
            )
            await sync_user(user_data, db)
            
        elif event_type == "organization.created":
            # Handle new organization creation
            org_data = ClerkOrganizationSync(
                clerk_org_id=data["id"],
                name=data["name"],
                slug=data.get("slug"),
                image_url=data.get("image_url"),
                members_count=data.get("members_count", 1),
            )
            await sync_organization(org_data, db)
            
        elif event_type in ["user.updated", "organization.updated"]:
            # Handle updates
            if "user" in event_type:
                # Update user
                pass
            else:
                # Update organization
                pass
        
        return {"success": True}
        
    except Exception as e:
        logger.error("Webhook processing failed", error=str(e), event_type=event_type)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )