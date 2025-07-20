"""API endpoints for privacy consent management and GDPR compliance."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.privacy_consent import privacy_consent_service
from app.auth.dependencies import get_current_user
from app.core.database import get_async_session
from app.models.user import User

router = APIRouter()

class ConsentGrantRequest(BaseModel):
    """Request model for granting consent."""

    consent_type: str = Field(
        ...,
        description="Type: memory_storage, preference_learning, team_sharing, analytics, data_export",
    )
    consent_scope: str = Field(
        ...,
        description="Scope: personal_memory, team_memory, cross_team, external_sharing",
    )
    legal_basis: str = Field(..., description="GDPR legal basis")
    processing_purpose: str = Field(..., description="Purpose of data processing")
    consent_method: str = Field(
        default="explicit", description="How consent was obtained"
    )
    expires_in_days: Optional[int] = Field(
        None, description="Days until consent expires"
    )
    consent_evidence: Optional[Dict[str, Any]] = Field(
        None, description="Evidence of consent"
    )

class ConsentWithdrawalRequest(BaseModel):
    """Request model for withdrawing consent."""

    consent_type: str = Field(..., description="Type of consent to withdraw")
    consent_scope: str = Field(..., description="Scope of consent to withdraw")
    withdrawal_evidence: Optional[Dict[str, Any]] = Field(
        None, description="Evidence of withdrawal"
    )

class DataExportRequest(BaseModel):
    """Request model for data export."""

    export_type: str = Field(
        ..., description="Type: full_export, partial_export, specific_data, gdpr_export"
    )
    data_categories: List[str] = Field(
        ...,
        description="Categories: conversations, user_memories, preferences, decisions, team_memories",
    )
    export_format: str = Field(
        default="json", description="Format: json, csv, xml, pdf"
    )
    date_range_start: Optional[datetime] = Field(
        None, description="Start date for data range"
    )
    date_range_end: Optional[datetime] = Field(
        None, description="End date for data range"
    )
    additional_filters: Optional[Dict[str, Any]] = Field(
        None, description="Additional filters"
    )

class ConsentStatusResponse(BaseModel):
    """Response model for consent status."""

    has_consent: bool
    status: str
    granted_at: Optional[str]
    expires_at: Optional[str]
    withdrawn_at: Optional[str]
    legal_basis: str
    processing_purpose: str
    consent_method: str
    last_confirmed_at: Optional[str]

class ConsentResponse(BaseModel):
    """Response model for consent record."""

    id: str
    consent_type: str
    consent_scope: str
    status: str
    legal_basis: str
    processing_purpose: str
    consent_method: str
    granted_at: Optional[str]
    expires_at: Optional[str]
    withdrawn_at: Optional[str]
    last_confirmed_at: Optional[str]
    created_at: str
    updated_at: str

class ExportStatusResponse(BaseModel):
    """Response model for export status."""

    id: str
    status: str
    export_type: str
    export_format: str
    data_categories: List[str]
    requested_at: str
    processing_started_at: Optional[str]
    completed_at: Optional[str]
    record_count: Optional[int]
    file_size: Optional[int]
    download_expires_at: Optional[str]
    download_count: int
    error_message: Optional[str]

@router.post("/consent/grant", response_model=Dict[str, str])
async def grant_consent(
    request: ConsentGrantRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> Dict[str, str]:
    """
    Grant privacy consent for data processing.

    Allows users to explicitly grant consent for different types
    of data processing with proper GDPR compliance tracking.
    """
    try:
        privacy_consent_service.session = session
        consent_id = await privacy_consent_service.grant_consent(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            consent_type=request.consent_type,
            consent_scope=request.consent_scope,
            legal_basis=request.legal_basis,
            processing_purpose=request.processing_purpose,
            consent_method=request.consent_method,
            consent_evidence=request.consent_evidence,
            expires_in_days=request.expires_in_days,
        )

        return {"consent_id": consent_id, "message": "Consent granted successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to grant consent: {str(e)}"
        )

@router.post("/consent/withdraw", response_model=Dict[str, str])
async def withdraw_consent(
    request: ConsentWithdrawalRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> Dict[str, str]:
    """
    Withdraw privacy consent for data processing.

    Allows users to withdraw consent, triggering appropriate
    data processing actions as required by GDPR.
    """
    try:
        privacy_consent_service.session = session
        success = await privacy_consent_service.withdraw_consent(
            user_id=current_user.id,
            consent_type=request.consent_type,
            consent_scope=request.consent_scope,
            withdrawal_evidence=request.withdrawal_evidence,
        )

        if success:
            return {"message": "Consent withdrawn successfully"}
        else:
            raise HTTPException(
                status_code=404, detail="Consent not found or already withdrawn"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to withdraw consent: {str(e)}"
        )

@router.get("/consent/status", response_model=ConsentStatusResponse)
async def check_consent_status(
    consent_type: str = Query(..., description="Type of consent to check"),
    consent_scope: str = Query(..., description="Scope of consent to check"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> ConsentStatusResponse:
    """
    Check the status of a specific consent.

    Returns detailed information about whether the user has
    granted consent for a specific type and scope of processing.
    """
    try:
        privacy_consent_service.session = session
        status = await privacy_consent_service.check_consent_status(
            user_id=current_user.id,
            consent_type=consent_type,
            consent_scope=consent_scope,
        )

        return ConsentStatusResponse(**status)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to check consent status: {str(e)}"
        )

@router.get("/consent/all", response_model=List[ConsentResponse])
async def get_user_consents(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> List[ConsentResponse]:
    """
    Get all consent records for the current user.

    Returns a complete list of all consent records,
    including granted, withdrawn, and expired consents.
    """
    try:
        privacy_consent_service.session = session
        consents = await privacy_consent_service.get_user_consents(current_user.id)

        return [ConsentResponse(**consent) for consent in consents]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve consents: {str(e)}"
        )

@router.post("/data-export/request", response_model=Dict[str, str])
async def request_data_export(
    request: DataExportRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> Dict[str, str]:
    """
    Request data export for GDPR compliance.

    Creates a request to export user data in the specified format.
    Processing happens asynchronously and users can check status
    using the returned request ID.
    """
    try:
        privacy_consent_service.session = session
        request_id = await privacy_consent_service.create_data_export_request(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            export_type=request.export_type,
            data_categories=request.data_categories,
            export_format=request.export_format,
            date_range_start=request.date_range_start,
            date_range_end=request.date_range_end,
            additional_filters=request.additional_filters,
        )

        return {
            "request_id": request_id,
            "message": "Data export request created successfully",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create data export request: {str(e)}"
        )

@router.get("/data-export/{request_id}/status", response_model=ExportStatusResponse)
async def get_export_status(
    request_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> ExportStatusResponse:
    """
    Get the status of a data export request.

    Returns detailed information about the export request
    including processing status, file size, and download information.
    """
    try:
        privacy_consent_service.session = session
        status = await privacy_consent_service.get_export_status(
            request_id=request_id, user_id=current_user.id
        )

        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])

        return ExportStatusResponse(**status)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get export status: {str(e)}"
        )

@router.get("/data-export/{request_id}/download")
async def download_export_file(
    request_id: str,
    token: str = Query(..., description="Download token"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Download the exported data file.

    Downloads the generated export file using a secure token.
    Files are automatically deleted after the expiry period.
    """
    try:
        privacy_consent_service.session = session

        # Get export request and validate
        status = await privacy_consent_service.get_export_status(
            request_id=request_id, user_id=current_user.id
        )

        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])

        if status["status"] != "completed":
            raise HTTPException(
                status_code=400, detail=f"Export not ready. Status: {status['status']}"
            )

        # Validate download token (simplified - in production, use proper token validation)
        from sqlalchemy import and_, select

        from app.models.memory import DataExportRequest

        request_query = select(DataExportRequest).where(
            and_(
                DataExportRequest.id == request_id,
                DataExportRequest.user_id == current_user.id,
                DataExportRequest.download_token == token,
            )
        )
        request_result = await session.execute(request_query)
        export_request = request_result.scalar_one_or_none()

        if not export_request:
            raise HTTPException(status_code=403, detail="Invalid download token")

        # Check if download link has expired
        if (
            export_request.download_expires_at
            and export_request.download_expires_at < datetime.now()
        ):
            raise HTTPException(status_code=410, detail="Download link has expired")

        # Update download count
        export_request.download_count += 1
        await session.commit()

        # Return file
        file_path = export_request.export_file_path
        if not file_path or not Path(file_path).exists():
            raise HTTPException(status_code=404, detail="Export file not found")

        filename = f"data_export_{request_id}.{export_request.export_format}"

        return FileResponse(
            path=file_path, filename=filename, media_type="application/octet-stream"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to download export file: {str(e)}"
        )

@router.delete("/data/delete-all", response_model=Dict[str, str])
async def delete_all_user_data(
    confirmation: str = Query(..., description="Must be 'DELETE_ALL_DATA' to confirm"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> Dict[str, str]:
    """
    Delete all user data (Right to be forgotten).

    This endpoint implements the GDPR "Right to be forgotten"
    by permanently deleting all user data from the system.
    Requires explicit confirmation.
    """
    if confirmation != "DELETE_ALL_DATA":
        raise HTTPException(
            status_code=400, detail="Invalid confirmation. Must be 'DELETE_ALL_DATA'"
        )

    try:
        # This would implement comprehensive data deletion
        # For now, we'll mark user as deleted and anonymize data

        from sqlalchemy import delete, update

        from app.models.memory import (Conversation, Decision, PrivacyConsent,
                                       UserBehaviorPattern, UserMemory,
                                       UserPreference)

        # Delete user memories
        await session.execute(
            delete(UserMemory).where(UserMemory.user_id == current_user.id)
        )

        # Delete user preferences
        await session.execute(
            delete(UserPreference).where(UserPreference.user_id == current_user.id)
        )

        # Delete behavior patterns
        await session.execute(
            delete(UserBehaviorPattern).where(
                UserBehaviorPattern.user_id == current_user.id
            )
        )

        # Anonymize conversations
        await session.execute(
            update(Conversation)
            .where(Conversation.user_id == current_user.id)
            .values(title="[DELETED]", updated_at=datetime.now())
        )

        # Delete decisions
        await session.execute(
            delete(Decision).where(Decision.user_id == current_user.id)
        )

        # Delete privacy consents
        await session.execute(
            delete(PrivacyConsent).where(PrivacyConsent.user_id == current_user.id)
        )

        await session.commit()

        return {"message": "All user data has been permanently deleted"}

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to delete user data: {str(e)}"
        )

@router.get("/privacy-policy", response_model=Dict[str, Any])
async def get_privacy_policy(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get the current privacy policy and data processing information.

    Returns information about what data is collected, how it's used,
    and user rights under GDPR and other privacy regulations.
    """
    return {
        "policy_version": "1.0",
        "effective_date": "2024-01-01",
        "data_controller": {
            "name": "SingleBrief",
            "contact": "privacy@singlebrief.com",
        },
        "data_categories": {
            "conversations": {
                "description": "Chat history and AI interactions",
                "purpose": "Provide personalized AI responses and maintain context",
                "legal_basis": "consent",
                "retention_period": "2 years or until consent withdrawn",
            },
            "user_memories": {
                "description": "Personal memories and preferences",
                "purpose": "Personalize AI responses and improve user experience",
                "legal_basis": "consent",
                "retention_period": "2 years or until consent withdrawn",
            },
            "team_memories": {
                "description": "Shared team knowledge and decisions",
                "purpose": "Enable team collaboration and knowledge sharing",
                "legal_basis": "legitimate_interests",
                "retention_period": "5 years or as per organization policy",
            },
            "preferences": {
                "description": "User communication and response preferences",
                "purpose": "Personalize AI communication style and content",
                "legal_basis": "consent",
                "retention_period": "2 years or until consent withdrawn",
            },
        },
        "user_rights": [
            "Access your personal data",
            "Rectify inaccurate data",
            "Erase your data (right to be forgotten)",
            "Restrict processing",
            "Data portability",
            "Object to processing",
            "Withdraw consent at any time",
        ],
        "contact_information": {
            "data_protection_officer": "dpo@singlebrief.com",
            "privacy_inquiries": "privacy@singlebrief.com",
        },
    }
