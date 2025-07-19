"""
User management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db_session
from app.models.user import User
from app.schemas.user import UserResponse, UserProfile, UserUpdate
from app.auth.dependencies import get_current_active_user, require_admin

router = APIRouter()


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get current user's full profile"""
    # TODO: Implement full profile with organization and teams
    return UserProfile.from_orm(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update current user's profile"""
    try:
        # Update user fields
        if user_update.full_name is not None:
            current_user.full_name = user_update.full_name
        if user_update.avatar_url is not None:
            current_user.avatar_url = user_update.avatar_url
        if user_update.privacy_settings is not None:
            current_user.privacy_settings = user_update.privacy_settings
        
        await db.commit()
        await db.refresh(current_user)
        
        return UserResponse.from_orm(current_user)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session)
):
    """List all users (admin only)"""
    try:
        result = await db.execute(
            select(User)
            .where(User.organization_id == current_user.organization_id)
            .offset(skip)
            .limit(limit)
        )
        users = result.scalars().all()
        
        return [UserResponse.from_orm(user) for user in users]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get user by ID"""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if current user can access this user
        if str(current_user.id) != user_id and not current_user.is_admin:
            # TODO: Check team membership
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user"
        )