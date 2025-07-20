"""Privacy Consent Management Service for SingleBrief.

This module implements GDPR-compliant privacy consent management,
data retention policies, and data export functionality for user memory data.
"""

from typing import Any, Dict, List, Optional, Tuple

import csv
import hashlib
import logging
import secrets
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.models.memory import (Conversation, ConversationMessage,
                               DataExportRequest, DataRetentionPolicy,
                               Decision, PrivacyConsent, TeamMemory,
                               UserBehaviorPattern, UserMemory, UserPreference)
from app.models.user import User

logger = logging.getLogger(__name__)

class PrivacyConsentService:
    """Service for managing privacy consent and GDPR compliance."""

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
        self.export_storage_path = Path("/tmp/exports")  # Should be configurable
        self.export_storage_path.mkdir(exist_ok=True)
        self.default_consent_expiry_days = 365  # Default consent validity

    async def grant_consent(
        self,
        user_id: str,
        organization_id: str,
        consent_type: str,
        consent_scope: str,
        legal_basis: str,
        processing_purpose: str,
        consent_method: str = "explicit",
        consent_evidence: Optional[Dict[str, Any]] = None,
        expires_in_days: Optional[int] = None,
    ) -> str:
        """Grant privacy consent for a user.

        Args:
            user_id: ID of the user granting consent
            organization_id: ID of the organization
            consent_type: Type of consent being granted
            consent_scope: Scope of the consent
            legal_basis: GDPR legal basis for processing
            processing_purpose: Purpose of data processing
            consent_method: How consent was obtained
            consent_evidence: Evidence of consent (IP, timestamp, etc.)
            expires_in_days: Days until consent expires

        Returns:
            ID of the created consent record
        """
        session = self.session or await get_async_session().__anext__()

        try:
            # Calculate expiry date
            expires_at = None
            if expires_in_days:
                expires_at = datetime.now(timezone.utc) + timedelta(
                    days=expires_in_days
                )
            elif self.default_consent_expiry_days > 0:
                expires_at = datetime.now(timezone.utc) + timedelta(
                    days=self.default_consent_expiry_days
                )

            # Check if consent already exists
            existing_query = select(PrivacyConsent).where(
                and_(
                    PrivacyConsent.user_id == user_id,
                    PrivacyConsent.consent_type == consent_type,
                    PrivacyConsent.consent_scope == consent_scope,
                )
            )
            existing_result = await session.execute(existing_query)
            existing_consent = existing_result.scalar_one_or_none()

            if existing_consent:
                # Update existing consent
                existing_consent.consent_status = "granted"
                existing_consent.legal_basis = legal_basis
                existing_consent.processing_purpose = processing_purpose
                existing_consent.consent_method = consent_method
                existing_consent.consent_evidence = consent_evidence
                existing_consent.granted_at = datetime.now(timezone.utc)
                existing_consent.expires_at = expires_at
                existing_consent.withdrawn_at = None
                existing_consent.last_confirmed_at = datetime.now(timezone.utc)
                existing_consent.updated_at = datetime.now(timezone.utc)

                consent_id = existing_consent.id
            else:
                # Create new consent
                new_consent = PrivacyConsent(
                    user_id=user_id,
                    organization_id=organization_id,
                    consent_type=consent_type,
                    consent_scope=consent_scope,
                    consent_status="granted",
                    legal_basis=legal_basis,
                    processing_purpose=processing_purpose,
                    consent_method=consent_method,
                    consent_evidence=consent_evidence,
                    expires_at=expires_at,
                    last_confirmed_at=datetime.now(timezone.utc),
                )

                session.add(new_consent)
                await session.flush()
                consent_id = new_consent.id

            await session.commit()

            logger.info(
                f"Granted consent {consent_id} for user {user_id}: {consent_type}/{consent_scope}"
            )
            return consent_id

        except Exception as e:
            logger.error(f"Error granting consent: {e}")
            await session.rollback()
            raise
        finally:
            if not self.session:
                await session.close()

    async def withdraw_consent(
        self,
        user_id: str,
        consent_type: str,
        consent_scope: str,
        withdrawal_evidence: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Withdraw privacy consent for a user.

        Args:
            user_id: ID of the user withdrawing consent
            consent_type: Type of consent being withdrawn
            consent_scope: Scope of the consent
            withdrawal_evidence: Evidence of withdrawal

        Returns:
            True if consent was withdrawn, False if not found
        """
        session = self.session or await get_async_session().__anext__()

        try:
            # Find existing consent
            consent_query = select(PrivacyConsent).where(
                and_(
                    PrivacyConsent.user_id == user_id,
                    PrivacyConsent.consent_type == consent_type,
                    PrivacyConsent.consent_scope == consent_scope,
                    PrivacyConsent.consent_status == "granted",
                )
            )
            consent_result = await session.execute(consent_query)
            consent = consent_result.scalar_one_or_none()

            if not consent:
                return False

            # Withdraw consent
            consent.consent_status = "withdrawn"
            consent.withdrawn_at = datetime.now(timezone.utc)
            consent.updated_at = datetime.now(timezone.utc)

            # Update evidence with withdrawal info
            if withdrawal_evidence:
                evidence = consent.consent_evidence or {}
                evidence["withdrawal"] = withdrawal_evidence
                consent.consent_evidence = evidence

            await session.commit()

            # Trigger data processing based on withdrawal
            await self._handle_consent_withdrawal(
                session, user_id, consent_type, consent_scope
            )

            logger.info(
                f"Withdrew consent for user {user_id}: {consent_type}/{consent_scope}"
            )
            return True

        except Exception as e:
            logger.error(f"Error withdrawing consent: {e}")
            await session.rollback()
            raise
        finally:
            if not self.session:
                await session.close()

    async def _handle_consent_withdrawal(
        self, session: AsyncSession, user_id: str, consent_type: str, consent_scope: str
    ) -> None:
        """Handle actions required when consent is withdrawn."""
        try:
            if consent_type == "memory_storage":
                if consent_scope == "personal_memory":
                    # Stop processing personal memories
                    await self._anonymize_personal_memories(session, user_id)
                elif consent_scope == "team_memory":
                    # Remove user from team memory validation
                    await self._remove_team_memory_participation(session, user_id)

            elif consent_type == "preference_learning":
                # Stop preference learning and optionally delete preferences
                await self._stop_preference_learning(session, user_id)

            elif consent_type == "analytics":
                # Anonymize user in analytics data
                await self._anonymize_analytics_data(session, user_id)

            await session.commit()

        except Exception as e:
            logger.error(f"Error handling consent withdrawal: {e}")
            raise

    async def _anonymize_personal_memories(
        self, session: AsyncSession, user_id: str
    ) -> None:
        """Anonymize personal memories when consent is withdrawn."""
        # Update user memories to anonymize personal information
        memories_query = select(UserMemory).where(
            and_(UserMemory.user_id == user_id, UserMemory.is_active == True)
        )
        memories_result = await session.execute(memories_query)
        memories = memories_result.scalars().all()

        for memory in memories:
            # Anonymize content while preserving structure
            memory.content = "[ANONYMIZED - Consent withdrawn]"
            memory.is_active = False
            memory.updated_at = datetime.now(timezone.utc)

    async def _remove_team_memory_participation(
        self, session: AsyncSession, user_id: str
    ) -> None:
        """Remove user participation from team memories."""
        # Remove user from team memory validation lists
        team_memories_query = select(TeamMemory).where(
            TeamMemory.validated_by_members.contains([user_id])
        )
        team_memories_result = await session.execute(team_memories_query)
        team_memories = team_memories_result.scalars().all()

        for memory in team_memories:
            validated_by = memory.validated_by_members or []
            if user_id in validated_by:
                validated_by.remove(user_id)
                memory.validated_by_members = validated_by
                memory.updated_at = datetime.now(timezone.utc)

    async def _stop_preference_learning(
        self, session: AsyncSession, user_id: str
    ) -> None:
        """Stop preference learning for user."""
        # Mark preferences as inactive
        await session.execute(
            update(UserPreference)
            .where(UserPreference.user_id == user_id)
            .values(is_active=False, updated_at=datetime.now(timezone.utc))
        )

        # Mark behavior patterns as inactive
        await session.execute(
            update(UserBehaviorPattern)
            .where(UserBehaviorPattern.user_id == user_id)
            .values(is_active=False, updated_at=datetime.now(timezone.utc))
        )

    async def _anonymize_analytics_data(
        self, session: AsyncSession, user_id: str
    ) -> None:
        """Anonymize user in analytics and reporting data."""
        # This would involve removing/anonymizing user data from analytics
        # For now, we'll mark conversations as anonymized
        await session.execute(
            update(Conversation)
            .where(Conversation.user_id == user_id)
            .values(title="[ANONYMIZED]", updated_at=datetime.now(timezone.utc))
        )

    async def check_consent_status(
        self, user_id: str, consent_type: str, consent_scope: str
    ) -> Dict[str, Any]:
        """Check the status of a user's consent.

        Args:
            user_id: ID of the user
            consent_type: Type of consent to check
            consent_scope: Scope of the consent

        Returns:
            Dict containing consent status and details
        """
        session = self.session or await get_async_session().__anext__()

        try:
            consent_query = select(PrivacyConsent).where(
                and_(
                    PrivacyConsent.user_id == user_id,
                    PrivacyConsent.consent_type == consent_type,
                    PrivacyConsent.consent_scope == consent_scope,
                )
            )
            consent_result = await session.execute(consent_query)
            consent = consent_result.scalar_one_or_none()

            if not consent:
                return {
                    "has_consent": False,
                    "status": "not_found",
                    "message": "No consent record found",
                }

            # Check if consent is still valid
            now = datetime.now(timezone.utc)
            is_expired = consent.expires_at and consent.expires_at < now

            if is_expired and consent.consent_status == "granted":
                # Update consent to expired
                consent.consent_status = "expired"
                consent.updated_at = now
                await session.commit()

            return {
                "has_consent": consent.consent_status == "granted" and not is_expired,
                "status": consent.consent_status,
                "granted_at": (
                    consent.granted_at.isoformat() if consent.granted_at else None
                ),
                "expires_at": (
                    consent.expires_at.isoformat() if consent.expires_at else None
                ),
                "withdrawn_at": (
                    consent.withdrawn_at.isoformat() if consent.withdrawn_at else None
                ),
                "legal_basis": consent.legal_basis,
                "processing_purpose": consent.processing_purpose,
                "consent_method": consent.consent_method,
                "last_confirmed_at": (
                    consent.last_confirmed_at.isoformat()
                    if consent.last_confirmed_at
                    else None
                ),
            }

        except Exception as e:
            logger.error(f"Error checking consent status: {e}")
            raise
        finally:
            if not self.session:
                await session.close()

    async def get_user_consents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all consents for a user.

        Args:
            user_id: ID of the user

        Returns:
            List of consent records
        """
        session = self.session or await get_async_session().__anext__()

        try:
            consents_query = (
                select(PrivacyConsent)
                .where(PrivacyConsent.user_id == user_id)
                .order_by(PrivacyConsent.created_at.desc())
            )

            consents_result = await session.execute(consents_query)
            consents = consents_result.scalars().all()

            formatted_consents = []
            for consent in consents:
                formatted_consents.append(
                    {
                        "id": consent.id,
                        "consent_type": consent.consent_type,
                        "consent_scope": consent.consent_scope,
                        "status": consent.consent_status,
                        "legal_basis": consent.legal_basis,
                        "processing_purpose": consent.processing_purpose,
                        "consent_method": consent.consent_method,
                        "granted_at": (
                            consent.granted_at.isoformat()
                            if consent.granted_at
                            else None
                        ),
                        "expires_at": (
                            consent.expires_at.isoformat()
                            if consent.expires_at
                            else None
                        ),
                        "withdrawn_at": (
                            consent.withdrawn_at.isoformat()
                            if consent.withdrawn_at
                            else None
                        ),
                        "last_confirmed_at": (
                            consent.last_confirmed_at.isoformat()
                            if consent.last_confirmed_at
                            else None
                        ),
                        "created_at": consent.created_at.isoformat(),
                        "updated_at": consent.updated_at.isoformat(),
                    }
                )

            return formatted_consents

        except Exception as e:
            logger.error(f"Error getting user consents: {e}")
            raise
        finally:
            if not self.session:
                await session.close()

    async def create_data_export_request(
        self,
        user_id: str,
        organization_id: str,
        export_type: str,
        data_categories: List[str],
        export_format: str = "json",
        date_range_start: Optional[datetime] = None,
        date_range_end: Optional[datetime] = None,
        additional_filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a data export request for GDPR compliance.

        Args:
            user_id: ID of the user requesting export
            organization_id: ID of the organization
            export_type: Type of export
            data_categories: Categories of data to export
            export_format: Format for the export
            date_range_start: Start date for data range
            date_range_end: End date for data range
            additional_filters: Additional filters

        Returns:
            ID of the created export request
        """
        session = self.session or await get_async_session().__anext__()

        try:
            # Generate secure download token
            download_token = secrets.token_urlsafe(32)
            download_expires_at = datetime.now(timezone.utc) + timedelta(
                days=7
            )  # 7-day expiry

            export_request = DataExportRequest(
                user_id=user_id,
                organization_id=organization_id,
                export_type=export_type,
                data_categories=data_categories,
                export_format=export_format,
                date_range_start=date_range_start,
                date_range_end=date_range_end,
                additional_filters=additional_filters,
                download_token=download_token,
                download_expires_at=download_expires_at,
            )

            session.add(export_request)
            await session.commit()
            await session.refresh(export_request)

            # Start background processing
            await self._process_data_export(session, export_request.id)

            logger.info(
                f"Created data export request {export_request.id} for user {user_id}"
            )
            return export_request.id

        except Exception as e:
            logger.error(f"Error creating data export request: {e}")
            await session.rollback()
            raise
        finally:
            if not self.session:
                await session.close()

    async def _process_data_export(
        self, session: AsyncSession, request_id: str
    ) -> None:
        """Process a data export request."""
        try:
            # Get export request
            request_query = select(DataExportRequest).where(
                DataExportRequest.id == request_id
            )
            request_result = await session.execute(request_query)
            export_request = request_result.scalar_one()

            # Update status to processing
            export_request.status = "processing"
            export_request.processing_started_at = datetime.now(timezone.utc)
            await session.commit()

            # Collect data based on categories
            export_data = await self._collect_export_data(session, export_request)

            # Generate export file
            file_path = await self._generate_export_file(export_request, export_data)

            # Update request with completion details
            export_request.status = "completed"
            export_request.completed_at = datetime.now(timezone.utc)
            export_request.export_file_path = str(file_path)
            export_request.export_file_size = file_path.stat().st_size
            export_request.record_count = len(export_data.get("records", []))

            await session.commit()

            logger.info(f"Completed data export request {request_id}")

        except Exception as e:
            logger.error(f"Error processing data export {request_id}: {e}")
            # Update request with error
            export_request.status = "failed"
            export_request.error_message = str(e)
            export_request.retry_count += 1
            await session.commit()

    async def _collect_export_data(
        self, session: AsyncSession, export_request: DataExportRequest
    ) -> Dict[str, Any]:
        """Collect data for export based on request parameters."""
        export_data = {
            "user_id": export_request.user_id,
            "export_type": export_request.export_type,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "records": [],
        }

        user_id = export_request.user_id
        date_start = export_request.date_range_start
        date_end = export_request.date_range_end

        for category in export_request.data_categories:
            if category == "conversations":
                conversations = await self._export_conversations(
                    session, user_id, date_start, date_end
                )
                export_data["conversations"] = conversations

            elif category == "user_memories":
                memories = await self._export_user_memories(
                    session, user_id, date_start, date_end
                )
                export_data["user_memories"] = memories

            elif category == "preferences":
                preferences = await self._export_preferences(
                    session, user_id, date_start, date_end
                )
                export_data["preferences"] = preferences

            elif category == "decisions":
                decisions = await self._export_decisions(
                    session, user_id, date_start, date_end
                )
                export_data["decisions"] = decisions

            elif category == "team_memories":
                team_memories = await self._export_team_memories(
                    session, user_id, date_start, date_end
                )
                export_data["team_memories"] = team_memories

        return export_data

    async def _export_conversations(
        self,
        session: AsyncSession,
        user_id: str,
        date_start: Optional[datetime],
        date_end: Optional[datetime],
    ) -> List[Dict[str, Any]]:
        """Export user conversations."""
        query = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.user_id == user_id)
        )

        if date_start:
            query = query.where(Conversation.created_at >= date_start)
        if date_end:
            query = query.where(Conversation.created_at <= date_end)

        result = await session.execute(query)
        conversations = result.scalars().all()

        exported_convs = []
        for conv in conversations:
            conv_data = {
                "id": conv.id,
                "title": conv.title,
                "context_type": conv.context_type,
                "created_at": conv.created_at.isoformat(),
                "messages": [],
            }

            for msg in conv.messages:
                msg_data = {
                    "id": msg.id,
                    "message_type": msg.message_type,
                    "content": msg.content,
                    "sequence_number": msg.sequence_number,
                    "created_at": msg.created_at.isoformat(),
                }
                conv_data["messages"].append(msg_data)

            exported_convs.append(conv_data)

        return exported_convs

    async def _export_user_memories(
        self,
        session: AsyncSession,
        user_id: str,
        date_start: Optional[datetime],
        date_end: Optional[datetime],
    ) -> List[Dict[str, Any]]:
        """Export user memories."""
        query = select(UserMemory).where(UserMemory.user_id == user_id)

        if date_start:
            query = query.where(UserMemory.created_at >= date_start)
        if date_end:
            query = query.where(UserMemory.created_at <= date_end)

        result = await session.execute(query)
        memories = result.scalars().all()

        exported_memories = []
        for memory in memories:
            memory_data = {
                "id": memory.id,
                "memory_type": memory.memory_type,
                "category": memory.category,
                "content": memory.content,
                "importance_score": memory.importance_score,
                "confidence_level": memory.confidence_level,
                "source": memory.source,
                "created_at": memory.created_at.isoformat(),
                "metadata": memory.memory_metadata,
            }
            exported_memories.append(memory_data)

        return exported_memories

    async def _export_preferences(
        self,
        session: AsyncSession,
        user_id: str,
        date_start: Optional[datetime],
        date_end: Optional[datetime],
    ) -> List[Dict[str, Any]]:
        """Export user preferences."""
        query = select(UserPreference).where(UserPreference.user_id == user_id)

        if date_start:
            query = query.where(UserPreference.created_at >= date_start)
        if date_end:
            query = query.where(UserPreference.created_at <= date_end)

        result = await session.execute(query)
        preferences = result.scalars().all()

        exported_prefs = []
        for pref in preferences:
            pref_data = {
                "id": pref.id,
                "preference_category": pref.preference_category,
                "preference_key": pref.preference_key,
                "preference_value": pref.preference_value,
                "confidence_score": pref.confidence_score,
                "learning_source": pref.learning_source,
                "is_manually_set": pref.is_manually_set,
                "created_at": pref.created_at.isoformat(),
            }
            exported_prefs.append(pref_data)

        return exported_prefs

    async def _export_decisions(
        self,
        session: AsyncSession,
        user_id: str,
        date_start: Optional[datetime],
        date_end: Optional[datetime],
    ) -> List[Dict[str, Any]]:
        """Export user decisions."""
        query = select(Decision).where(Decision.user_id == user_id)

        if date_start:
            query = query.where(Decision.decided_at >= date_start)
        if date_end:
            query = query.where(Decision.decided_at <= date_end)

        result = await session.execute(query)
        decisions = result.scalars().all()

        exported_decisions = []
        for decision in decisions:
            decision_data = {
                "id": decision.id,
                "title": decision.title,
                "description": decision.description,
                "decision_type": decision.decision_type,
                "priority_level": decision.priority_level,
                "status": decision.status,
                "outcome": decision.outcome,
                "decided_at": decision.decided_at.isoformat(),
                "context_tags": decision.context_tags,
            }
            exported_decisions.append(decision_data)

        return exported_decisions

    async def _export_team_memories(
        self,
        session: AsyncSession,
        user_id: str,
        date_start: Optional[datetime],
        date_end: Optional[datetime],
    ) -> List[Dict[str, Any]]:
        """Export team memories where user participated."""
        # Only export team memories where user was involved
        query = select(TeamMemory).where(
            or_(
                TeamMemory.created_by_user_id == user_id,
                TeamMemory.validated_by_members.contains([user_id]),
            )
        )

        if date_start:
            query = query.where(TeamMemory.created_at >= date_start)
        if date_end:
            query = query.where(TeamMemory.created_at <= date_end)

        result = await session.execute(query)
        team_memories = result.scalars().all()

        exported_team_memories = []
        for memory in team_memories:
            # Only include limited info for team memories
            memory_data = {
                "id": memory.id,
                "title": memory.title,
                "memory_type": memory.memory_type,
                "category": memory.category,
                "user_role": (
                    "creator" if memory.created_by_user_id == user_id else "validator"
                ),
                "consensus_level": memory.consensus_level,
                "created_at": memory.created_at.isoformat(),
            }
            exported_team_memories.append(memory_data)

        return exported_team_memories

    async def _generate_export_file(
        self, export_request: DataExportRequest, export_data: Dict[str, Any]
    ) -> Path:
        """Generate export file in requested format."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"data_export_{export_request.user_id}_{timestamp}"

        if export_request.export_format == "json":
            file_path = self.export_storage_path / f"{filename}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

        elif export_request.export_format == "csv":
            file_path = self.export_storage_path / f"{filename}.csv"
            await self._generate_csv_export(file_path, export_data)

        elif export_request.export_format == "xml":
            file_path = self.export_storage_path / f"{filename}.xml"
            await self._generate_xml_export(file_path, export_data)

        else:
            raise ValueError(
                f"Unsupported export format: {export_request.export_format}"
            )

        return file_path

    async def _generate_csv_export(
        self, file_path: Path, export_data: Dict[str, Any]
    ) -> None:
        """Generate CSV export file."""
        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            # Write header with metadata
            writer.writerow(["Data Export"])
            writer.writerow(["User ID", export_data["user_id"]])
            writer.writerow(["Generated At", export_data["generated_at"]])
            writer.writerow([])  # Empty row

            # Export each data category
            for category, data in export_data.items():
                if category in ["user_id", "export_type", "generated_at", "records"]:
                    continue

                if isinstance(data, list) and data:
                    writer.writerow([f"--- {category.upper()} ---"])

                    # Write headers based on first item
                    if data:
                        headers = list(data[0].keys())
                        writer.writerow(headers)

                        # Write data rows
                        for item in data:
                            row = [str(item.get(header, "")) for header in headers]
                            writer.writerow(row)

                    writer.writerow([])  # Empty row between categories

    async def _generate_xml_export(
        self, file_path: Path, export_data: Dict[str, Any]
    ) -> None:
        """Generate XML export file."""
        root = ET.Element("DataExport")

        # Add metadata
        metadata = ET.SubElement(root, "Metadata")
        ET.SubElement(metadata, "UserId").text = export_data["user_id"]
        ET.SubElement(metadata, "GeneratedAt").text = export_data["generated_at"]
        ET.SubElement(metadata, "ExportType").text = export_data["export_type"]

        # Add data categories
        for category, data in export_data.items():
            if category in ["user_id", "export_type", "generated_at", "records"]:
                continue

            if isinstance(data, list):
                category_elem = ET.SubElement(root, category.title())

                for item in data:
                    item_elem = ET.SubElement(
                        category_elem,
                        category[:-1] if category.endswith("s") else "item",
                    )

                    for key, value in item.items():
                        elem = ET.SubElement(item_elem, key)
                        elem.text = str(value) if value is not None else ""

        # Write to file
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        tree.write(file_path, encoding="utf-8", xml_declaration=True)

    async def get_export_status(self, request_id: str, user_id: str) -> Dict[str, Any]:
        """Get the status of a data export request.

        Args:
            request_id: ID of the export request
            user_id: ID of the user (for security)

        Returns:
            Dict containing export status and details
        """
        session = self.session or await get_async_session().__anext__()

        try:
            request_query = select(DataExportRequest).where(
                and_(
                    DataExportRequest.id == request_id,
                    DataExportRequest.user_id == user_id,
                )
            )
            request_result = await session.execute(request_query)
            export_request = request_result.scalar_one_or_none()

            if not export_request:
                return {"error": "Export request not found"}

            return {
                "id": export_request.id,
                "status": export_request.status,
                "export_type": export_request.export_type,
                "export_format": export_request.export_format,
                "data_categories": export_request.data_categories,
                "requested_at": export_request.requested_at.isoformat(),
                "processing_started_at": (
                    export_request.processing_started_at.isoformat()
                    if export_request.processing_started_at
                    else None
                ),
                "completed_at": (
                    export_request.completed_at.isoformat()
                    if export_request.completed_at
                    else None
                ),
                "record_count": export_request.record_count,
                "file_size": export_request.export_file_size,
                "download_expires_at": (
                    export_request.download_expires_at.isoformat()
                    if export_request.download_expires_at
                    else None
                ),
                "download_count": export_request.download_count,
                "error_message": export_request.error_message,
            }

        except Exception as e:
            logger.error(f"Error getting export status: {e}")
            raise
        finally:
            if not self.session:
                await session.close()

# Singleton instance for easy access
privacy_consent_service = PrivacyConsentService()
