"""
Organization management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db_session
from app.models.user import User, Organization
from app.schemas.user import OrganizationResponse, OrganizationUpdate
from app.auth.dependencies import get_current_active_user, require_admin

router = APIRouter()


@router.get("/me", response_model=OrganizationResponse)
async def get_current_organization(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get current user's organization"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not part of an organization"
        )
    
    try:
        result = await db.execute(
            select(Organization).where(Organization.id == current_user.organization_id)
        )
        organization = result.scalar_one_or_none()
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        return OrganizationResponse.from_orm(organization)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch organization"
        )


@router.put("/me", response_model=OrganizationResponse)
async def update_organization(
    org_update: OrganizationUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session)
):
    """Update organization (admin only)"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not part of an organization"
        )
    
    try:
        result = await db.execute(
            select(Organization).where(Organization.id == current_user.organization_id)
        )
        organization = result.scalar_one_or_none()
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Update organization fields
        if org_update.name is not None:
            organization.name = org_update.name
        if org_update.domain is not None:
            organization.domain = org_update.domain
        if org_update.data_retention_days is not None:
            organization.data_retention_days = org_update.data_retention_days
        
        await db.commit()
        await db.refresh(organization)
        
        return OrganizationResponse.from_orm(organization)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update organization"
        )