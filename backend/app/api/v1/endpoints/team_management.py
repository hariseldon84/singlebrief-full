"""
Team Member Profile Management API Endpoints for Story 7.1

Comprehensive API endpoints for:
- Team member profile creation, management, search and filtering
- Role and designation taxonomy management
- Custom expertise tags management
- Platform account integration and verification
- Team hierarchy management
- Bulk operations and CSV import
"""

import csv
import base64
import io
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy import select, and_, or_, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_active_user, require_manager
from app.core.database import get_db_session
from app.models.team_management import (
    TeamMemberProfileManagement, RoleTaxonomy, DesignationTaxonomy, 
    ExpertiseTag, TeamMemberPlatformAccount, TeamHierarchy, 
    TeamMemberStatusHistory, team_member_expertise_tags
)
from app.models.user import User, Team, Organization
from app.schemas.team_management import (
    # Team member profiles
    TeamMemberProfileCreate, TeamMemberProfileUpdate, TeamMemberProfileResponse,
    TeamMemberSearchRequest, TeamMemberSearchResponse, TeamMemberBulkCreate,
    TeamMemberImportCSV, BulkOperationResponse,
    # Taxonomy
    RoleTaxonomyCreate, RoleTaxonomyUpdate, RoleTaxonomyResponse,
    DesignationTaxonomyCreate, DesignationTaxonomyUpdate, DesignationTaxonomyResponse,
    ExpertiseTagCreate, ExpertiseTagUpdate, ExpertiseTagResponse,
    # Platform accounts and hierarchy
    PlatformAccountCreate, PlatformAccountUpdate, PlatformAccountResponse,
    TeamHierarchyCreate, TeamHierarchyUpdate, TeamHierarchyResponse,
    # Status and history
    StatusChangeCreate, StatusHistoryResponse,
    ExpertiseTagAssignment, MemberStatusEnum
)

router = APIRouter(prefix="/team-management", tags=["Team Management"])


# =====================================================================
# ROLE TAXONOMY MANAGEMENT
# =====================================================================

@router.get("/roles", response_model=List[RoleTaxonomyResponse])
async def list_roles(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    category: Optional[str] = None,
    is_active: bool = True,
):
    """List roles available to the user's organization"""
    try:
        query = select(RoleTaxonomy).where(
            and_(
                or_(
                    RoleTaxonomy.organization_id == current_user.organization_id,
                    RoleTaxonomy.is_system_role == True
                ),
                RoleTaxonomy.is_active == is_active
            )
        )
        
        if category:
            query = query.where(RoleTaxonomy.category == category)
            
        query = query.order_by(RoleTaxonomy.category, RoleTaxonomy.seniority_level, RoleTaxonomy.name)
        result = await db.execute(query)
        roles = result.scalars().all()
        
        return [RoleTaxonomyResponse.from_orm(role) for role in roles]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch roles: {str(e)}"
        )


@router.post("/roles", response_model=RoleTaxonomyResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleTaxonomyCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db_session),
):
    """Create custom role for organization"""
    try:
        role = RoleTaxonomy(
            **role_data.dict(),
            organization_id=current_user.organization_id,
            is_system_role=False
        )
        
        db.add(role)
        await db.commit()
        await db.refresh(role)
        
        return RoleTaxonomyResponse.from_orm(role)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create role: {str(e)}"
        )


# =====================================================================
# DESIGNATION TAXONOMY MANAGEMENT  
# =====================================================================

@router.get("/designations", response_model=List[DesignationTaxonomyResponse])
async def list_designations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    department: Optional[str] = None,
    is_active: bool = True,
):
    """List designations available to the user's organization"""
    try:
        query = select(DesignationTaxonomy).where(
            and_(
                or_(
                    DesignationTaxonomy.organization_id == current_user.organization_id,
                    DesignationTaxonomy.is_system_designation == True
                ),
                DesignationTaxonomy.is_active == is_active
            )
        )
        
        if department:
            query = query.where(DesignationTaxonomy.department == department)
            
        query = query.order_by(DesignationTaxonomy.hierarchy_level.desc(), DesignationTaxonomy.name)
        result = await db.execute(query)
        designations = result.scalars().all()
        
        return [DesignationTaxonomyResponse.from_orm(designation) for designation in designations]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch designations: {str(e)}"
        )


@router.post("/designations", response_model=DesignationTaxonomyResponse, status_code=status.HTTP_201_CREATED)
async def create_designation(
    designation_data: DesignationTaxonomyCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db_session),
):
    """Create custom designation for organization"""
    try:
        designation = DesignationTaxonomy(
            **designation_data.dict(),
            organization_id=current_user.organization_id,
            is_system_designation=False
        )
        
        db.add(designation)
        await db.commit()
        await db.refresh(designation)
        
        return DesignationTaxonomyResponse.from_orm(designation)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create designation: {str(e)}"
        )


# =====================================================================
# EXPERTISE TAGS MANAGEMENT
# =====================================================================

@router.get("/tags", response_model=List[ExpertiseTagResponse])
async def list_expertise_tags(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    category: Optional[str] = None,
    search: Optional[str] = None,
    is_active: bool = True,
):
    """List expertise tags available to the user's organization"""
    try:
        query = select(ExpertiseTag).where(
            and_(
                or_(
                    ExpertiseTag.organization_id == current_user.organization_id,
                    ExpertiseTag.is_system_tag == True
                ),
                ExpertiseTag.is_active == is_active
            )
        )
        
        if category:
            query = query.where(ExpertiseTag.category == category)
            
        if search:
            query = query.where(
                or_(
                    ExpertiseTag.name.ilike(f"%{search}%"),
                    ExpertiseTag.display_name.ilike(f"%{search}%"),
                    ExpertiseTag.description.ilike(f"%{search}%")
                )
            )
            
        query = query.order_by(ExpertiseTag.usage_count.desc(), ExpertiseTag.name)
        result = await db.execute(query)
        tags = result.scalars().all()
        
        return [ExpertiseTagResponse.from_orm(tag) for tag in tags]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tags: {str(e)}"
        )


@router.post("/tags", response_model=ExpertiseTagResponse, status_code=status.HTTP_201_CREATED)
async def create_expertise_tag(
    tag_data: ExpertiseTagCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db_session),
):
    """Create custom expertise tag for organization"""
    try:
        tag = ExpertiseTag(
            **tag_data.dict(),
            organization_id=current_user.organization_id,
            is_system_tag=False
        )
        
        db.add(tag)
        await db.commit()
        await db.refresh(tag)
        
        return ExpertiseTagResponse.from_orm(tag)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tag: {str(e)}"
        )


# =====================================================================
# TEAM MEMBER PROFILE MANAGEMENT
# =====================================================================

@router.post("/members", response_model=TeamMemberProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_team_member(
    member_data: TeamMemberProfileCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db_session),
):
    """Create team member profile"""
    try:
        # Verify team exists and user has access
        team_result = await db.execute(select(Team).where(Team.id == member_data.team_id))
        team = team_result.scalar_one_or_none()
        if not team or team.organization_id != current_user.organization_id:
            raise HTTPException(status_code=404, detail="Team not found")
            
        # Handle user creation/linking - for now, create placeholder user or use current user
        if member_data.user_id:
            user_result = await db.execute(select(User).where(User.id == member_data.user_id))
            user = user_result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            user_id = user.id
        else:
            # For simplified workflow, use current user as placeholder or create minimal user record
            user_id = current_user.id
            
        # Create team member profile
        member = TeamMemberProfileManagement(
            **{k: v for k, v in member_data.dict().items() 
               if k not in ['expertise_tags', 'platform_accounts', 'user_id']},
            user_id=user_id,
            organization_id=current_user.organization_id
        )
        
        db.add(member)
        await db.flush()  # Get the ID
        
        # Handle expertise tags - create user-defined tags on the fly
        for tag_assignment in member_data.expertise_tags:
            # Check if this is a user-defined tag (starts with 'user-tag-')
            if tag_assignment.tag_id.startswith('user-tag-'):
                # Extract tag name from the assignment
                tag_name = tag_assignment.tag_name if hasattr(tag_assignment, 'tag_name') else tag_assignment.tag_id.replace('user-tag-', '')
                
                # Create or find existing user-defined tag
                existing_tag_result = await db.execute(
                    select(ExpertiseTag).where(
                        and_(
                            ExpertiseTag.name == tag_name,
                            ExpertiseTag.organization_id == current_user.organization_id,
                            ExpertiseTag.is_system_tag == False
                        )
                    )
                )
                existing_tag = existing_tag_result.scalar_one_or_none()
                
                if not existing_tag:
                    # Create new user-defined tag
                    new_tag = ExpertiseTag(
                        name=tag_name,
                        display_name=tag_name,
                        category="user_defined",
                        organization_id=current_user.organization_id,
                        is_system_tag=False
                    )
                    db.add(new_tag)
                    await db.flush()
                    tag_id = new_tag.id
                else:
                    tag_id = existing_tag.id
            else:
                tag_id = tag_assignment.tag_id
                
            await db.execute(
                team_member_expertise_tags.insert().values(
                    team_member_id=member.id,
                    expertise_tag_id=tag_id,
                    proficiency_level=tag_assignment.proficiency_level
                )
            )
        
        # Add platform accounts
        for platform_data in member_data.platform_accounts:
            platform_account = TeamMemberPlatformAccount(
                **platform_data.dict(),
                team_member_id=member.id
            )
            db.add(platform_account)
            
        await db.commit()
        
        # Reload with relationships
        result = await db.execute(
            select(TeamMemberProfileManagement)
            .options(
                selectinload(TeamMemberProfileManagement.role),
                selectinload(TeamMemberProfileManagement.designation),
                selectinload(TeamMemberProfileManagement.expertise_tags),
                selectinload(TeamMemberProfileManagement.platform_accounts)
            )
            .where(TeamMemberProfileManagement.id == member.id)
        )
        member = result.scalar_one()
        
        return TeamMemberProfileResponse.from_orm(member)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create team member: {str(e)}"
        )


@router.get("/members/search", response_model=TeamMemberSearchResponse)
async def search_team_members(
    search_params: TeamMemberSearchRequest = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Search and filter team members"""
    try:
        # Base query with joins
        query = select(TeamMemberProfileManagement).options(
            selectinload(TeamMemberProfileManagement.role),
            selectinload(TeamMemberProfileManagement.designation),
            selectinload(TeamMemberProfileManagement.expertise_tags),
            selectinload(TeamMemberProfileManagement.platform_accounts)
        ).where(
            TeamMemberProfileManagement.organization_id == current_user.organization_id
        )
        
        # Apply filters
        filters = []
        
        if search_params.search_query:
            search_term = f"%{search_params.search_query}%"
            filters.append(
                or_(
                    TeamMemberProfileManagement.custom_role.ilike(search_term),
                    TeamMemberProfileManagement.custom_designation.ilike(search_term),
                    TeamMemberProfileManagement.bio.ilike(search_term),
                    TeamMemberProfileManagement.skills_summary.ilike(search_term),
                    TeamMemberProfileManagement.notes.ilike(search_term)
                )
            )
            
        if search_params.team_ids:
            filters.append(TeamMemberProfileManagement.team_id.in_(search_params.team_ids))
            
        if search_params.role_ids:
            filters.append(TeamMemberProfileManagement.role_id.in_(search_params.role_ids))
            
        if search_params.designation_ids:
            filters.append(TeamMemberProfileManagement.designation_id.in_(search_params.designation_ids))
            
        if search_params.statuses:
            filters.append(TeamMemberProfileManagement.status.in_([s.value for s in search_params.statuses]))
            
        if search_params.min_capacity is not None:
            filters.append(TeamMemberProfileManagement.capacity_percentage >= search_params.min_capacity)
        if search_params.max_capacity is not None:
            filters.append(TeamMemberProfileManagement.capacity_percentage <= search_params.max_capacity)
            
        if search_params.min_workload is not None:
            filters.append(TeamMemberProfileManagement.current_workload >= search_params.min_workload)
        if search_params.max_workload is not None:
            filters.append(TeamMemberProfileManagement.current_workload <= search_params.max_workload)
            
        if search_params.slack_verified is not None:
            filters.append(TeamMemberProfileManagement.slack_verified == search_params.slack_verified)
        if search_params.teams_verified is not None:
            filters.append(TeamMemberProfileManagement.teams_verified == search_params.teams_verified)
        if search_params.email_verified is not None:
            filters.append(TeamMemberProfileManagement.email_verified == search_params.email_verified)
            
        if search_params.created_after:
            filters.append(TeamMemberProfileManagement.created_at >= search_params.created_after)
        if search_params.created_before:
            filters.append(TeamMemberProfileManagement.created_at <= search_params.created_before)
            
        if filters:
            query = query.where(and_(*filters))
            
        # Handle expertise tag filtering separately (requires join)
        if search_params.expertise_tag_ids:
            query = query.join(team_member_expertise_tags).where(
                team_member_expertise_tags.c.expertise_tag_id.in_(search_params.expertise_tag_ids)
            )
            
        # Count total before pagination
        count_query = select(func.count(distinct(TeamMemberProfileManagement.id))).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # Apply sorting
        if search_params.sort_by == "name":
            sort_column = TeamMemberProfileManagement.custom_role  # Could join with User for actual name
        elif search_params.sort_by == "created_at":
            sort_column = TeamMemberProfileManagement.created_at
        elif search_params.sort_by == "updated_at":
            sort_column = TeamMemberProfileManagement.updated_at
        elif search_params.sort_by == "response_quality_score":
            sort_column = TeamMemberProfileManagement.response_quality_score
        elif search_params.sort_by == "average_response_time_hours":
            sort_column = TeamMemberProfileManagement.average_response_time_hours
        else:
            sort_column = TeamMemberProfileManagement.created_at
            
        if search_params.sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
            
        # Apply pagination
        query = query.offset(search_params.skip).limit(search_params.limit)
        
        result = await db.execute(query)
        members = result.scalars().all()
        
        return TeamMemberSearchResponse(
            total=total,
            skip=search_params.skip,
            limit=search_params.limit,
            results=[TeamMemberProfileResponse.from_orm(member) for member in members]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search team members: {str(e)}"
        )


@router.get("/members/{member_id}", response_model=TeamMemberProfileResponse)
async def get_team_member(
    member_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get team member profile by ID"""
    try:
        result = await db.execute(
            select(TeamMemberProfileManagement)
            .options(
                selectinload(TeamMemberProfileManagement.role),
                selectinload(TeamMemberProfileManagement.designation),
                selectinload(TeamMemberProfileManagement.expertise_tags),
                selectinload(TeamMemberProfileManagement.platform_accounts)
            )
            .where(
                and_(
                    TeamMemberProfileManagement.id == member_id,
                    TeamMemberProfileManagement.organization_id == current_user.organization_id
                )
            )
        )
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(status_code=404, detail="Team member not found")
            
        return TeamMemberProfileResponse.from_orm(member)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch team member: {str(e)}"
        )


@router.put("/members/{member_id}", response_model=TeamMemberProfileResponse)
async def update_team_member(
    member_id: str,
    member_update: TeamMemberProfileUpdate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db_session),
):
    """Update team member profile"""
    try:
        # Get existing member
        result = await db.execute(
            select(TeamMemberProfileManagement)
            .where(
                and_(
                    TeamMemberProfileManagement.id == member_id,
                    TeamMemberProfileManagement.organization_id == current_user.organization_id
                )
            )
        )
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(status_code=404, detail="Team member not found")
            
        # Update fields
        update_data = member_update.dict(exclude_unset=True, exclude={'expertise_tags'})
        for field, value in update_data.items():
            setattr(member, field, value)
            
        # Handle expertise tags replacement if provided
        if member_update.expertise_tags is not None:
            # Remove existing tags
            await db.execute(
                team_member_expertise_tags.delete().where(
                    team_member_expertise_tags.c.team_member_id == member_id
                )
            )
            
            # Add new tags
            for tag_assignment in member_update.expertise_tags:
                await db.execute(
                    team_member_expertise_tags.insert().values(
                        team_member_id=member_id,
                        expertise_tag_id=tag_assignment.tag_id,
                        proficiency_level=tag_assignment.proficiency_level
                    )
                )
                
        await db.commit()
        
        # Reload with relationships
        result = await db.execute(
            select(TeamMemberProfileManagement)
            .options(
                selectinload(TeamMemberProfileManagement.role),
                selectinload(TeamMemberProfileManagement.designation),
                selectinload(TeamMemberProfileManagement.expertise_tags),
                selectinload(TeamMemberProfileManagement.platform_accounts)
            )
            .where(TeamMemberProfileManagement.id == member_id)
        )
        member = result.scalar_one()
        
        return TeamMemberProfileResponse.from_orm(member)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update team member: {str(e)}"
        )


# =====================================================================
# BULK OPERATIONS
# =====================================================================

@router.post("/members/bulk", response_model=BulkOperationResponse, status_code=status.HTTP_201_CREATED)
async def bulk_create_team_members(
    bulk_data: TeamMemberBulkCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db_session),
):
    """Bulk create team members"""
    try:
        created_ids = []
        errors = []
        
        for i, member_data in enumerate(bulk_data.team_members):
            try:
                # Create member (reuse single creation logic)
                member = TeamMemberProfileManagement(
                    **{k: v for k, v in member_data.dict().items() 
                       if k not in ['expertise_tags', 'platform_accounts']},
                    organization_id=current_user.organization_id
                )
                
                db.add(member)
                await db.flush()
                
                # Add expertise tags and platform accounts
                for tag_assignment in member_data.expertise_tags:
                    await db.execute(
                        team_member_expertise_tags.insert().values(
                            team_member_id=member.id,
                            expertise_tag_id=tag_assignment.tag_id,
                            proficiency_level=tag_assignment.proficiency_level
                        )
                    )
                    
                for platform_data in member_data.platform_accounts:
                    platform_account = TeamMemberPlatformAccount(
                        **platform_data.dict(),
                        team_member_id=member.id
                    )
                    db.add(platform_account)
                    
                created_ids.append(member.id)
                
            except Exception as e:
                errors.append({
                    "index": i,
                    "error": str(e),
                    "user_id": member_data.user_id
                })
                
        await db.commit()
        
        return BulkOperationResponse(
            total_records=len(bulk_data.team_members),
            successful=len(created_ids),
            failed=len(errors),
            errors=errors,
            created_ids=created_ids
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk creation failed: {str(e)}"
        )


@router.post("/members/import-csv", response_model=BulkOperationResponse)
async def import_team_members_csv(
    import_data: TeamMemberImportCSV,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db_session),
):
    """Import team members from CSV"""
    try:
        # Decode CSV data
        csv_content = base64.b64decode(import_data.csv_data).decode('utf-8')
        csv_file = io.StringIO(csv_content)
        csv_reader = csv.DictReader(csv_file)
        
        if import_data.skip_header:
            next(csv_reader, None)
            
        created_ids = []
        errors = []
        row_index = 0
        
        for row in csv_reader:
            try:
                # Map CSV columns to member fields using column_mapping
                member_data = {}
                for csv_col, field_name in import_data.column_mapping.items():
                    if csv_col in row and row[csv_col]:
                        member_data[field_name] = row[csv_col]
                        
                # Create basic member (extend this logic based on CSV structure)
                member = TeamMemberProfileManagement(
                    team_id=import_data.team_id,
                    organization_id=current_user.organization_id,
                    **member_data
                )
                
                db.add(member)
                await db.flush()
                created_ids.append(member.id)
                
            except Exception as e:
                errors.append({
                    "index": row_index,
                    "error": str(e),
                    "row_data": dict(row)
                })
                
            row_index += 1
            
        await db.commit()
        
        return BulkOperationResponse(
            total_records=row_index,
            successful=len(created_ids),
            failed=len(errors),
            errors=errors,
            created_ids=created_ids
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CSV import failed: {str(e)}"
        )


# =====================================================================
# TEAM HIERARCHY MANAGEMENT
# =====================================================================

@router.post("/hierarchy", response_model=TeamHierarchyResponse, status_code=status.HTTP_201_CREATED)
async def create_hierarchy_relationship(
    hierarchy_data: TeamHierarchyCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db_session),
):
    """Create team hierarchy relationship"""
    try:
        hierarchy = TeamHierarchy(**hierarchy_data.dict())
        db.add(hierarchy)
        await db.commit()
        await db.refresh(hierarchy)
        
        return TeamHierarchyResponse.from_orm(hierarchy)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create hierarchy: {str(e)}"
        )


@router.get("/members/{member_id}/status-history", response_model=List[StatusHistoryResponse])
async def get_member_status_history(
    member_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get status change history for team member"""
    try:
        result = await db.execute(
            select(TeamMemberStatusHistory)
            .where(TeamMemberStatusHistory.team_member_id == member_id)
            .order_by(TeamMemberStatusHistory.effective_from.desc())
        )
        history = result.scalars().all()
        
        return [StatusHistoryResponse.from_orm(entry) for entry in history]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch status history: {str(e)}"
        )


@router.post("/members/{member_id}/status", response_model=StatusHistoryResponse, status_code=status.HTTP_201_CREATED)
async def change_member_status(
    member_id: str,
    status_change: StatusChangeCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db_session),
):
    """Change team member status"""
    try:
        # Get current member status
        member_result = await db.execute(
            select(TeamMemberProfileManagement)
            .where(
                and_(
                    TeamMemberProfileManagement.id == member_id,
                    TeamMemberProfileManagement.organization_id == current_user.organization_id
                )
            )
        )
        member = member_result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(status_code=404, detail="Team member not found")
            
        # Create status history entry
        status_history = TeamMemberStatusHistory(
            team_member_id=member_id,
            from_status=member.status,
            to_status=status_change.to_status,
            reason=status_change.reason,
            notes=status_change.notes,
            changed_by_user_id=current_user.id,
            change_source="manual",
            effective_from=status_change.effective_from
        )
        
        # Update member status
        member.status = status_change.to_status
        
        db.add(status_history)
        await db.commit()
        await db.refresh(status_history)
        
        return StatusHistoryResponse.from_orm(status_history)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change status: {str(e)}"
        )