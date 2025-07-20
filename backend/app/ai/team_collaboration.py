"""Team Memory and Collaboration Context Service for SingleBrief.

This module implements team-level memory management, consensus tracking,
role-based access controls, and collaborative context building for teams.
"""

from typing import Any, Dict, List, Optional, Tuple

import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from enum import Enum

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.models.memory import (Conversation, ConversationMessage, TeamMemory,
                               UserMemory)
from app.models.user import Team, TeamMember, User

logger = logging.getLogger(__name__)

class ConsensusLevel(Enum):
    """Consensus levels for team memory validation."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNANIMOUS = "unanimous"

class AccessLevel(Enum):
    """Access levels for team memory."""

    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN_ONLY = "admin_only"

class TeamCollaborationService:
    """Service for managing team memory and collaboration context."""

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
        self.consensus_thresholds = {
            ConsensusLevel.LOW: 0.3,
            ConsensusLevel.MEDIUM: 0.6,
            ConsensusLevel.HIGH: 0.8,
            ConsensusLevel.UNANIMOUS: 1.0,
        }
        self.memory_retention_days = 90  # Default retention for team memories

    async def create_team_memory(
        self,
        team_id: str,
        created_by_user_id: str,
        title: str,
        content: str,
        memory_type: str,
        category: str,
        metadata: Optional[Dict[str, Any]] = None,
        visibility: str = "team",
        access_level: str = "read_write",
    ) -> str:
        """Create a new team memory.

        Args:
            team_id: ID of the team
            created_by_user_id: ID of the user creating the memory
            title: Memory title
            content: Memory content
            memory_type: Type of memory (team_process, decision_pattern, etc.)
            category: Category for organizing memories
            metadata: Additional metadata
            visibility: Memory visibility level
            access_level: Access level for the memory

        Returns:
            ID of the created team memory
        """
        session = self.session or await get_async_session().__anext__()

        try:
            # Get team organization
            team_query = select(Team).where(Team.id == team_id)
            team_result = await session.execute(team_query)
            team = team_result.scalar_one()

            # Create team memory
            team_memory = TeamMemory(
                team_id=team_id,
                organization_id=team.organization_id,
                created_by_user_id=created_by_user_id,
                title=title,
                content=content,
                memory_type=memory_type,
                category=category,
                team_metadata=metadata or {},
                visibility=visibility,
                access_level=access_level,
                source="team_discussion",
            )

            session.add(team_memory)
            await session.commit()
            await session.refresh(team_memory)

            logger.info(f"Created team memory {team_memory.id} for team {team_id}")
            return team_memory.id

        except Exception as e:
            logger.error(f"Error creating team memory: {e}")
            await session.rollback()
            raise
        finally:
            if not self.session:
                await session.close()

    async def validate_team_memory(
        self, memory_id: str, validating_user_id: str, is_valid: bool = True
    ) -> Dict[str, Any]:
        """Validate a team memory by a team member.

        Args:
            memory_id: ID of the team memory
            validating_user_id: ID of the user providing validation
            is_valid: Whether the user considers the memory valid

        Returns:
            Dict containing updated validation status
        """
        session = self.session or await get_async_session().__anext__()

        try:
            # Get team memory
            memory_query = select(TeamMemory).where(TeamMemory.id == memory_id)
            memory_result = await session.execute(memory_query)
            memory = memory_result.scalar_one()

            # Check if user is team member
            member_query = select(TeamMember).where(
                and_(
                    TeamMember.team_id == memory.team_id,
                    TeamMember.user_id == validating_user_id,
                    TeamMember.is_active == True,
                )
            )
            member_result = await session.execute(member_query)
            member = member_result.scalar_one_or_none()

            if not member:
                raise ValueError("User is not a member of this team")

            # Update validation list
            validated_by = memory.validated_by_members or []
            if is_valid and validating_user_id not in validated_by:
                validated_by.append(validating_user_id)
            elif not is_valid and validating_user_id in validated_by:
                validated_by.remove(validating_user_id)

            # Get total team members
            team_size_query = select(func.count(TeamMember.id)).where(
                and_(TeamMember.team_id == memory.team_id, TeamMember.is_active == True)
            )
            team_size_result = await session.execute(team_size_query)
            team_size = team_size_result.scalar()

            # Calculate consensus level
            consensus_score = len(validated_by) / max(team_size, 1)
            consensus_level = self._calculate_consensus_level(consensus_score)

            # Update memory
            memory.validated_by_members = validated_by
            memory.consensus_level = consensus_score
            memory.relevance_score = (
                min(memory.relevance_score + 0.1, 1.0)
                if is_valid
                else max(memory.relevance_score - 0.1, 0.0)
            )
            memory.updated_at = datetime.now(timezone.utc)

            await session.commit()

            return {
                "memory_id": memory_id,
                "consensus_score": consensus_score,
                "consensus_level": consensus_level.value,
                "validated_by_count": len(validated_by),
                "team_size": team_size,
                "relevance_score": memory.relevance_score,
            }

        except Exception as e:
            logger.error(f"Error validating team memory: {e}")
            await session.rollback()
            raise
        finally:
            if not self.session:
                await session.close()

    def _calculate_consensus_level(self, consensus_score: float) -> ConsensusLevel:
        """Calculate consensus level based on score."""
        if consensus_score >= self.consensus_thresholds[ConsensusLevel.UNANIMOUS]:
            return ConsensusLevel.UNANIMOUS
        elif consensus_score >= self.consensus_thresholds[ConsensusLevel.HIGH]:
            return ConsensusLevel.HIGH
        elif consensus_score >= self.consensus_thresholds[ConsensusLevel.MEDIUM]:
            return ConsensusLevel.MEDIUM
        else:
            return ConsensusLevel.LOW

    async def get_team_memories(
        self,
        team_id: str,
        user_id: str,
        category: Optional[str] = None,
        memory_type: Optional[str] = None,
        min_consensus: Optional[float] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get team memories with role-based filtering.

        Args:
            team_id: ID of the team
            user_id: ID of the requesting user
            category: Optional category filter
            memory_type: Optional memory type filter
            min_consensus: Minimum consensus level required
            limit: Maximum number of memories to return

        Returns:
            List of team memories the user can access
        """
        session = self.session or await get_async_session().__anext__()

        try:
            # Check user's role in team
            member_query = select(TeamMember).where(
                and_(
                    TeamMember.team_id == team_id,
                    TeamMember.user_id == user_id,
                    TeamMember.is_active == True,
                )
            )
            member_result = await session.execute(member_query)
            member = member_result.scalar_one_or_none()

            if not member:
                raise ValueError("User is not a member of this team")

            # Build query based on access permissions
            query = select(TeamMemory).where(
                and_(TeamMemory.team_id == team_id, TeamMemory.is_active == True)
            )

            # Apply role-based filtering
            if member.role not in ["team_lead", "admin"]:
                # Regular members can only see non-admin memories
                query = query.where(TeamMemory.access_level != "admin_only")

            # Apply filters
            if category:
                query = query.where(TeamMemory.category == category)
            if memory_type:
                query = query.where(TeamMemory.memory_type == memory_type)
            if min_consensus is not None:
                query = query.where(TeamMemory.consensus_level >= min_consensus)

            # Order by relevance and importance
            query = query.order_by(
                TeamMemory.relevance_score.desc(),
                TeamMemory.importance_score.desc(),
                TeamMemory.updated_at.desc(),
            ).limit(limit)

            result = await session.execute(query)
            memories = result.scalars().all()

            # Format response
            formatted_memories = []
            for memory in memories:
                formatted_memories.append(
                    {
                        "id": memory.id,
                        "title": memory.title,
                        "content": memory.content,
                        "memory_type": memory.memory_type,
                        "category": memory.category,
                        "importance_score": memory.importance_score,
                        "relevance_score": memory.relevance_score,
                        "consensus_level": memory.consensus_level,
                        "consensus_status": self._calculate_consensus_level(
                            memory.consensus_level
                        ).value,
                        "validated_by_count": len(memory.validated_by_members or []),
                        "visibility": memory.visibility,
                        "access_level": memory.access_level,
                        "created_at": memory.created_at.isoformat(),
                        "updated_at": memory.updated_at.isoformat(),
                        "metadata": memory.team_metadata,
                    }
                )

            return formatted_memories

        except Exception as e:
            logger.error(f"Error getting team memories: {e}")
            raise
        finally:
            if not self.session:
                await session.close()

    async def analyze_team_interaction_patterns(self, team_id: str) -> Dict[str, Any]:
        """Analyze team interaction patterns and collaboration dynamics.

        Args:
            team_id: ID of the team to analyze

        Returns:
            Dict containing team interaction analysis
        """
        session = self.session or await get_async_session().__anext__()

        try:
            # Get team conversations from the last 30 days
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

            conv_query = (
                select(Conversation)
                .options(selectinload(Conversation.messages))
                .where(
                    and_(
                        Conversation.team_id == team_id,
                        Conversation.created_at >= cutoff_date,
                    )
                )
            )

            conv_result = await session.execute(conv_query)
            conversations = conv_result.scalars().all()

            # Analyze patterns
            interaction_analysis = {
                "communication_frequency": self._analyze_communication_frequency(
                    conversations
                ),
                "participation_patterns": await self._analyze_participation_patterns(
                    session, team_id, conversations
                ),
                "collaboration_effectiveness": self._analyze_collaboration_effectiveness(
                    conversations
                ),
                "knowledge_sharing": await self._analyze_knowledge_sharing(
                    session, team_id
                ),
                "decision_patterns": await self._analyze_decision_patterns(
                    session, team_id
                ),
                "team_health_indicators": await self._calculate_team_health_indicators(
                    session, team_id
                ),
            }

            return interaction_analysis

        except Exception as e:
            logger.error(f"Error analyzing team interaction patterns: {e}")
            raise
        finally:
            if not self.session:
                await session.close()

    def _analyze_communication_frequency(
        self, conversations: List[Conversation]
    ) -> Dict[str, Any]:
        """Analyze communication frequency patterns."""
        daily_conversations = defaultdict(int)
        hourly_patterns = defaultdict(int)

        for conv in conversations:
            day = conv.created_at.date()
            hour = conv.created_at.hour
            daily_conversations[day] += 1
            hourly_patterns[hour] += 1

        # Calculate metrics
        total_days = len(daily_conversations) if daily_conversations else 1
        avg_daily_conversations = sum(daily_conversations.values()) / total_days

        peak_hour = (
            max(hourly_patterns.items(), key=lambda x: x[1])[0]
            if hourly_patterns
            else 9
        )

        return {
            "total_conversations": len(conversations),
            "average_daily_conversations": avg_daily_conversations,
            "peak_communication_hour": peak_hour,
            "communication_distribution": dict(hourly_patterns),
            "active_days": len(daily_conversations),
        }

    async def _analyze_participation_patterns(
        self, session: AsyncSession, team_id: str, conversations: List[Conversation]
    ) -> Dict[str, Any]:
        """Analyze team member participation patterns."""
        # Get team members
        members_query = (
            select(TeamMember)
            .options(selectinload(TeamMember.user))
            .where(and_(TeamMember.team_id == team_id, TeamMember.is_active == True))
        )
        members_result = await session.execute(members_query)
        team_members = members_result.scalars().all()

        # Analyze participation
        member_participation = defaultdict(lambda: {"conversations": 0, "messages": 0})

        for conv in conversations:
            user_id = conv.user_id
            member_participation[user_id]["conversations"] += 1
            member_participation[user_id]["messages"] += len(conv.messages)

        # Calculate participation metrics
        total_members = len(team_members)
        active_members = len(member_participation)
        participation_rate = active_members / max(total_members, 1)

        # Find most and least active members
        sorted_participation = sorted(
            member_participation.items(),
            key=lambda x: x[1]["conversations"],
            reverse=True,
        )

        return {
            "total_team_members": total_members,
            "active_members": active_members,
            "participation_rate": participation_rate,
            "member_activity": dict(member_participation),
            "most_active_member": (
                sorted_participation[0][0] if sorted_participation else None
            ),
            "participation_balance": self._calculate_participation_balance(
                member_participation
            ),
        }

    def _calculate_participation_balance(
        self, participation: Dict[str, Dict[str, int]]
    ) -> float:
        """Calculate how balanced participation is across team members."""
        if not participation:
            return 0.0

        conversation_counts = [data["conversations"] for data in participation.values()]
        if not conversation_counts:
            return 0.0

        mean_conversations = sum(conversation_counts) / len(conversation_counts)
        variance = sum(
            (x - mean_conversations) ** 2 for x in conversation_counts
        ) / len(conversation_counts)

        # Return balance score (higher = more balanced)
        return max(0.0, 1.0 - (variance / max(mean_conversations, 1)))

    def _analyze_collaboration_effectiveness(
        self, conversations: List[Conversation]
    ) -> Dict[str, Any]:
        """Analyze collaboration effectiveness metrics."""
        total_messages = sum(len(conv.messages) for conv in conversations)
        avg_messages_per_conversation = total_messages / max(len(conversations), 1)

        # Analyze conversation depths
        conversation_depths = [len(conv.messages) for conv in conversations]
        avg_depth = sum(conversation_depths) / max(len(conversation_depths), 1)

        # Analyze response times (simplified)
        quick_responses = 0
        total_responses = 0

        for conv in conversations:
            messages = sorted(conv.messages, key=lambda m: m.created_at)
            for i in range(1, len(messages)):
                time_diff = (
                    messages[i].created_at - messages[i - 1].created_at
                ).total_seconds()
                total_responses += 1
                if time_diff < 3600:  # Less than 1 hour
                    quick_responses += 1

        response_rate = quick_responses / max(total_responses, 1)

        return {
            "average_conversation_depth": avg_depth,
            "average_messages_per_conversation": avg_messages_per_conversation,
            "quick_response_rate": response_rate,
            "total_collaborative_sessions": len(conversations),
        }

    async def _analyze_knowledge_sharing(
        self, session: AsyncSession, team_id: str
    ) -> Dict[str, Any]:
        """Analyze knowledge sharing patterns within the team."""
        # Get team memories created in the last 30 days
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

        memories_query = select(TeamMemory).where(
            and_(
                TeamMemory.team_id == team_id,
                TeamMemory.created_at >= cutoff_date,
                TeamMemory.is_active == True,
            )
        )

        memories_result = await session.execute(memories_query)
        memories = memories_result.scalars().all()

        # Analyze knowledge sharing metrics
        knowledge_categories = defaultdict(int)
        knowledge_sources = defaultdict(int)

        for memory in memories:
            knowledge_categories[memory.category] += 1
            knowledge_sources[memory.source] += 1

        return {
            "knowledge_items_created": len(memories),
            "knowledge_categories": dict(knowledge_categories),
            "knowledge_sources": dict(knowledge_sources),
            "average_consensus": sum(m.consensus_level for m in memories)
            / max(len(memories), 1),
            "validated_knowledge_ratio": sum(
                1 for m in memories if m.consensus_level > 0.5
            )
            / max(len(memories), 1),
        }

    async def _analyze_decision_patterns(
        self, session: AsyncSession, team_id: str
    ) -> Dict[str, Any]:
        """Analyze team decision-making patterns."""
        from app.models.memory import Decision

        # Get team decisions from the last 60 days
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=60)

        decisions_query = select(Decision).where(
            and_(Decision.team_id == team_id, Decision.decided_at >= cutoff_date)
        )

        decisions_result = await session.execute(decisions_query)
        decisions = decisions_result.scalars().all()

        # Analyze decision patterns
        decision_types = defaultdict(int)
        decision_outcomes = defaultdict(int)

        for decision in decisions:
            decision_types[decision.decision_type] += 1
            decision_outcomes[decision.status] += 1

        # Calculate decision velocity
        implemented_decisions = [d for d in decisions if d.implemented_at]
        avg_implementation_time = 0

        if implemented_decisions:
            implementation_times = [
                (d.implemented_at - d.decided_at).days
                for d in implemented_decisions
                if d.implemented_at and d.decided_at
            ]
            avg_implementation_time = sum(implementation_times) / len(
                implementation_times
            )

        return {
            "total_decisions": len(decisions),
            "decision_types": dict(decision_types),
            "decision_outcomes": dict(decision_outcomes),
            "implementation_rate": len(implemented_decisions) / max(len(decisions), 1),
            "average_implementation_days": avg_implementation_time,
        }

    async def _calculate_team_health_indicators(
        self, session: AsyncSession, team_id: str
    ) -> Dict[str, Any]:
        """Calculate overall team health indicators."""
        # Get team size and active members
        members_query = select(func.count(TeamMember.id)).where(
            and_(TeamMember.team_id == team_id, TeamMember.is_active == True)
        )
        members_result = await session.execute(members_query)
        team_size = members_result.scalar()

        # Get team memory validation rates
        memories_query = select(TeamMemory).where(
            and_(TeamMemory.team_id == team_id, TeamMemory.is_active == True)
        )
        memories_result = await session.execute(memories_query)
        memories = memories_result.scalars().all()

        if memories:
            avg_consensus = sum(m.consensus_level for m in memories) / len(memories)
            high_consensus_ratio = sum(
                1 for m in memories if m.consensus_level > 0.7
            ) / len(memories)
        else:
            avg_consensus = 0.0
            high_consensus_ratio = 0.0

        # Calculate overall health score
        health_score = (
            avg_consensus * 0.4
            + high_consensus_ratio * 0.3
            + min(team_size / 5, 1.0) * 0.3
        )

        return {
            "team_size": team_size,
            "average_consensus": avg_consensus,
            "high_consensus_ratio": high_consensus_ratio,
            "overall_health_score": health_score,
            "health_status": (
                "excellent"
                if health_score > 0.8
                else "good" if health_score > 0.6 else "needs_attention"
            ),
        }

    async def update_memory_permissions(
        self,
        memory_id: str,
        user_id: str,
        new_visibility: Optional[str] = None,
        new_access_level: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update memory permissions (team leads and admins only).

        Args:
            memory_id: ID of the team memory
            user_id: ID of the user making the change
            new_visibility: New visibility level
            new_access_level: New access level

        Returns:
            Dict containing updated memory information
        """
        session = self.session or await get_async_session().__anext__()

        try:
            # Get memory and check permissions
            memory_query = select(TeamMemory).where(TeamMemory.id == memory_id)
            memory_result = await session.execute(memory_query)
            memory = memory_result.scalar_one()

            # Check if user has permission to modify
            member_query = select(TeamMember).where(
                and_(
                    TeamMember.team_id == memory.team_id,
                    TeamMember.user_id == user_id,
                    TeamMember.is_active == True,
                )
            )
            member_result = await session.execute(member_query)
            member = member_result.scalar_one_or_none()

            if not member or member.role not in ["team_lead", "admin"]:
                raise ValueError(
                    "User does not have permission to modify memory permissions"
                )

            # Update permissions
            if new_visibility:
                memory.visibility = new_visibility
            if new_access_level:
                memory.access_level = new_access_level

            memory.updated_at = datetime.now(timezone.utc)

            await session.commit()

            return {
                "memory_id": memory_id,
                "visibility": memory.visibility,
                "access_level": memory.access_level,
                "updated_by": user_id,
                "updated_at": memory.updated_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error updating memory permissions: {e}")
            await session.rollback()
            raise
        finally:
            if not self.session:
                await session.close()

    async def cross_team_memory_sharing(
        self,
        source_team_id: str,
        target_team_id: str,
        memory_id: str,
        requesting_user_id: str,
        sharing_permissions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Enable cross-team memory sharing.

        Args:
            source_team_id: ID of the team sharing the memory
            target_team_id: ID of the team receiving access
            memory_id: ID of the memory to share
            requesting_user_id: ID of the user requesting the sharing
            sharing_permissions: Permissions and access controls

        Returns:
            Dict containing sharing details
        """
        session = self.session or await get_async_session().__anext__()

        try:
            # Verify user has permission to share from source team
            source_member_query = select(TeamMember).where(
                and_(
                    TeamMember.team_id == source_team_id,
                    TeamMember.user_id == requesting_user_id,
                    TeamMember.is_active == True,
                )
            )
            source_member_result = await session.execute(source_member_query)
            source_member = source_member_result.scalar_one_or_none()

            if not source_member or source_member.role not in ["team_lead", "admin"]:
                raise ValueError(
                    "User does not have permission to share from source team"
                )

            # Get the memory
            memory_query = select(TeamMemory).where(TeamMemory.id == memory_id)
            memory_result = await session.execute(memory_query)
            memory = memory_result.scalar_one()

            # Update memory metadata to include cross-team sharing
            sharing_metadata = memory.team_metadata or {}
            shared_with = sharing_metadata.get("shared_with_teams", [])

            if target_team_id not in shared_with:
                shared_with.append(target_team_id)
                sharing_metadata["shared_with_teams"] = shared_with
                sharing_metadata["sharing_permissions"] = sharing_permissions

                memory.team_metadata = sharing_metadata
                memory.updated_at = datetime.now(timezone.utc)

                await session.commit()

            return {
                "memory_id": memory_id,
                "source_team_id": source_team_id,
                "target_team_id": target_team_id,
                "shared_at": datetime.now(timezone.utc).isoformat(),
                "shared_by": requesting_user_id,
                "permissions": sharing_permissions,
            }

        except Exception as e:
            logger.error(f"Error sharing memory across teams: {e}")
            await session.rollback()
            raise
        finally:
            if not self.session:
                await session.close()

# Singleton instance for easy access
team_collaboration_service = TeamCollaborationService()
