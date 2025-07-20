"""Memory Engine database models for SingleBrief.

This module contains all database models related to the Memory Engine system,
including conversations, decisions, user memories, and team memories.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (JSON, Boolean, CheckConstraint, Column, DateTime,
                        ForeignKey, Index, Integer, String, Text,
                        UniqueConstraint)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

class Conversation(Base):
    """Stores conversation history for team leads and AI interactions.

    This model tracks all conversations between users and the AI system,
    providing context for future interactions and memory building.
    """

    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
    )
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Conversation metadata
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    context_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of conversation: daily_brief, ad_hoc_query, team_interrogation",
    )
    session_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Privacy and consent
    is_shared_with_team: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    retention_policy: Mapped[str] = mapped_column(
        String(50),
        default="standard",
        comment="Retention policy: standard, extended, permanent, delete_on_request",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="conversations")
    team: Mapped[Optional["Team"]] = relationship(
        "Team", back_populates="conversations"
    )
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="conversations"
    )
    messages: Mapped[List["ConversationMessage"]] = relationship(
        "ConversationMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.created_at",
    )
    decisions: Mapped[List["Decision"]] = relationship(
        "Decision", back_populates="conversation", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        Index("idx_conversations_user_created", "user_id", "created_at"),
        Index("idx_conversations_team_created", "team_id", "created_at"),
        Index("idx_conversations_context_type", "context_type"),
        Index("idx_conversations_session", "session_id"),
        CheckConstraint(
            "context_type IN ('daily_brief', 'ad_hoc_query', 'team_interrogation', 'memory_query')",
            name="check_conversation_context_type",
        ),
        CheckConstraint(
            "retention_policy IN ('standard', 'extended', 'permanent', 'delete_on_request')",
            name="check_retention_policy",
        ),
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title='{self.title}', user_id={self.user_id})>"

class ConversationMessage(Base):
    """Individual messages within a conversation.

    Stores the actual message content, metadata, and AI response data
    for each turn in a conversation.
    """

    __tablename__ = "conversation_messages"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    conversation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Message content
    message_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Type: user_query, ai_response, system_message",
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, comment="Additional metadata like response time, confidence scores, etc."
    )

    # AI-specific fields
    ai_model_used: Mapped[Optional[str]] = mapped_column(String(100))
    confidence_score: Mapped[Optional[float]] = mapped_column()
    sources_used: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB, comment="Sources and data used to generate response"
    )
    processing_time_ms: Mapped[Optional[int]] = mapped_column()

    # Message ordering and timing
    sequence_number: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )

    # Constraints
    __table_args__ = (
        Index(
            "idx_conversation_messages_conv_seq", "conversation_id", "sequence_number"
        ),
        Index("idx_conversation_messages_created", "created_at"),
        UniqueConstraint(
            "conversation_id",
            "sequence_number",
            name="uq_conversation_message_sequence",
        ),
        CheckConstraint(
            "message_type IN ('user_query', 'ai_response', 'system_message')",
            name="check_message_type",
        ),
        CheckConstraint(
            "confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)",
            name="check_confidence_score_range",
        ),
    )

    def __repr__(self) -> str:
        return f"<ConversationMessage(id={self.id}, type={self.message_type}, seq={self.sequence_number})>"

class Decision(Base):
    """Tracks decisions made during conversations and their outcomes.

    This model captures important decisions for future reference and
    helps build organizational memory.
    """

    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    conversation_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
    )
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Decision content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    decision_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type: strategic, operational, personnel, technical, process",
    )
    priority_level: Mapped[str] = mapped_column(
        String(20), default="medium", comment="Priority: low, medium, high, critical"
    )

    # Decision status and outcomes
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        comment="Status: pending, approved, implemented, cancelled, reviewed",
    )
    outcome: Mapped[Optional[str]] = mapped_column(Text)
    impact_assessment: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, comment="Assessment of decision impact and results"
    )

    # Stakeholders and context
    stakeholders: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, comment="List of user IDs affected by this decision"
    )
    context_tags: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, comment="Tags for categorization and search"
    )

    # Timing
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    implementation_deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    implemented_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    conversation: Mapped[Optional["Conversation"]] = relationship(
        "Conversation", back_populates="decisions"
    )
    user: Mapped["User"] = relationship("User", back_populates="decisions")
    team: Mapped[Optional["Team"]] = relationship("Team", back_populates="decisions")
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="decisions"
    )

    # Constraints
    __table_args__ = (
        Index("idx_decisions_user_decided", "user_id", "decided_at"),
        Index("idx_decisions_team_decided", "team_id", "decided_at"),
        Index("idx_decisions_status", "status"),
        Index("idx_decisions_type", "decision_type"),
        Index("idx_decisions_priority", "priority_level"),
        CheckConstraint(
            "decision_type IN ('strategic', 'operational', 'personnel', 'technical', 'process')",
            name="check_decision_type",
        ),
        CheckConstraint(
            "priority_level IN ('low', 'medium', 'high', 'critical')",
            name="check_priority_level",
        ),
        CheckConstraint(
            "status IN ('pending', 'approved', 'implemented', 'cancelled', 'reviewed')",
            name="check_decision_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<Decision(id={self.id}, title='{self.title}', status={self.status})>"

class UserMemory(Base):
    """Individual user memories for personalization.

    Stores user-specific memories that help personalize AI responses
    and maintain context across sessions.
    """

    __tablename__ = "user_memories"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Memory content
    memory_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type: preference, behavior_pattern, context, personal_info, work_style",
    )
    category: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Category for organizing memories"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    memory_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, comment="Additional structured data and context"
    )

    # Memory properties
    importance_score: Mapped[float] = mapped_column(
        default=0.5, comment="Importance score 0.0-1.0 for memory prioritization"
    )
    confidence_level: Mapped[float] = mapped_column(
        default=0.5, comment="Confidence in memory accuracy 0.0-1.0"
    )
    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Source: conversation, explicit_input, inferred, external_integration",
    )

    # Privacy and sharing
    is_private: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Whether memory is private to user or can be shared",
    )
    sharing_level: Mapped[str] = mapped_column(
        String(20),
        default="private",
        comment="Sharing level: private, team, organization",
    )

    # Memory lifecycle
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    access_count: Mapped[int] = mapped_column(default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_memories")
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="user_memories"
    )
    embeddings: Mapped[List["MemoryEmbedding"]] = relationship(
        "MemoryEmbedding", back_populates="user_memory", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        Index("idx_user_memories_user_created", "user_id", "created_at"),
        Index("idx_user_memories_type", "memory_type"),
        Index("idx_user_memories_category", "category"),
        Index("idx_user_memories_importance", "importance_score"),
        Index("idx_user_memories_active", "is_active"),
        CheckConstraint(
            "memory_type IN ('preference', 'behavior_pattern', 'context', 'personal_info', 'work_style')",
            name="check_user_memory_type",
        ),
        CheckConstraint(
            "importance_score >= 0.0 AND importance_score <= 1.0",
            name="check_importance_score_range",
        ),
        CheckConstraint(
            "confidence_level >= 0.0 AND confidence_level <= 1.0",
            name="check_confidence_level_range",
        ),
        CheckConstraint(
            "sharing_level IN ('private', 'team', 'organization')",
            name="check_sharing_level",
        ),
        CheckConstraint(
            "source IN ('conversation', 'explicit_input', 'inferred', 'external_integration')",
            name="check_memory_source",
        ),
    )

    def __repr__(self) -> str:
        return f"<UserMemory(id={self.id}, type={self.memory_type}, category='{self.category}')>"

class TeamMemory(Base):
    """Shared team memories for collaboration context.

    Stores team-level memories that provide context for team interactions
    and help maintain team-specific knowledge.
    """

    __tablename__ = "team_memories"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    team_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_by_user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Memory content
    memory_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type: team_process, decision_pattern, collaboration_style, project_context",
    )
    category: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Category for organizing team memories"
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    team_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, comment="Additional structured data and context"
    )

    # Memory properties
    importance_score: Mapped[float] = mapped_column(
        default=0.5, comment="Importance score 0.0-1.0 for memory prioritization"
    )
    relevance_score: Mapped[float] = mapped_column(
        default=0.5, comment="Current relevance score 0.0-1.0"
    )
    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Source: team_discussion, decision, process_observation, external_input",
    )

    # Team consensus and validation
    consensus_level: Mapped[float] = mapped_column(
        default=0.5, comment="Team consensus on memory accuracy 0.0-1.0"
    )
    validated_by_members: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, comment="List of user IDs who have validated this memory"
    )

    # Visibility and access
    visibility: Mapped[str] = mapped_column(
        String(20), default="team", comment="Visibility: team, organization, private"
    )
    access_level: Mapped[str] = mapped_column(
        String(20),
        default="read_write",
        comment="Access level: read_only, read_write, admin_only",
    )

    # Memory lifecycle
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    access_count: Mapped[int] = mapped_column(default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    team: Mapped["Team"] = relationship("Team", back_populates="team_memories")
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="team_memories"
    )
    created_by: Mapped["User"] = relationship(
        "User", back_populates="created_team_memories"
    )
    embeddings: Mapped[List["MemoryEmbedding"]] = relationship(
        "MemoryEmbedding", back_populates="team_memory", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        Index("idx_team_memories_team_created", "team_id", "created_at"),
        Index("idx_team_memories_type", "memory_type"),
        Index("idx_team_memories_category", "category"),
        Index("idx_team_memories_importance", "importance_score"),
        Index("idx_team_memories_active", "is_active"),
        CheckConstraint(
            "memory_type IN ('team_process', 'decision_pattern', 'collaboration_style', 'project_context')",
            name="check_team_memory_type",
        ),
        CheckConstraint(
            "importance_score >= 0.0 AND importance_score <= 1.0",
            name="check_team_importance_score_range",
        ),
        CheckConstraint(
            "relevance_score >= 0.0 AND relevance_score <= 1.0",
            name="check_relevance_score_range",
        ),
        CheckConstraint(
            "consensus_level >= 0.0 AND consensus_level <= 1.0",
            name="check_consensus_level_range",
        ),
        CheckConstraint(
            "visibility IN ('team', 'organization', 'private')",
            name="check_team_memory_visibility",
        ),
        CheckConstraint(
            "access_level IN ('read_only', 'read_write', 'admin_only')",
            name="check_team_memory_access_level",
        ),
        CheckConstraint(
            "source IN ('team_discussion', 'decision', 'process_observation', 'external_input')",
            name="check_team_memory_source",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<TeamMemory(id={self.id}, title='{self.title}', team_id={self.team_id})>"
        )

class UserPreference(Base):
    """User preferences and learning data for personalization.

    Tracks user communication style, topic interests, and behavioral patterns
    to enable personalized AI responses and content delivery.
    """

    __tablename__ = "user_preferences"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Preference category and type
    preference_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Category: communication_style, topic_interest, format_preference, timing, feedback",
    )
    preference_key: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Specific preference identifier"
    )
    preference_value: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, comment="Preference value and related metadata"
    )

    # Learning and confidence metrics
    confidence_score: Mapped[float] = mapped_column(
        default=0.5, comment="Confidence in preference accuracy 0.0-1.0"
    )
    learning_source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Source: explicit_feedback, behavioral_analysis, pattern_detection, manual_override",
    )
    evidence_count: Mapped[int] = mapped_column(
        default=1, comment="Number of evidence points supporting this preference"
    )

    # Adaptation tracking
    last_evidence_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="When last evidence was collected",
    )
    adaptation_rate: Mapped[float] = mapped_column(
        default=0.1, comment="Rate of preference adaptation 0.0-1.0"
    )
    stability_score: Mapped[float] = mapped_column(
        default=0.5, comment="Stability of preference over time 0.0-1.0"
    )

    # Override and manual control
    is_manually_set: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Whether preference was manually set by user"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="preferences")
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="user_preferences"
    )

    # Constraints
    __table_args__ = (
        Index("idx_user_preferences_user_category", "user_id", "preference_category"),
        Index("idx_user_preferences_key", "preference_key"),
        Index("idx_user_preferences_confidence", "confidence_score"),
        Index("idx_user_preferences_updated", "updated_at"),
        UniqueConstraint(
            "user_id",
            "preference_category",
            "preference_key",
            name="uq_user_preference",
        ),
        CheckConstraint(
            "preference_category IN ('communication_style', 'topic_interest', 'format_preference', 'timing', 'feedback')",
            name="check_preference_category",
        ),
        CheckConstraint(
            "confidence_score >= 0.0 AND confidence_score <= 1.0",
            name="check_preference_confidence_score_range",
        ),
        CheckConstraint(
            "adaptation_rate >= 0.0 AND adaptation_rate <= 1.0",
            name="check_adaptation_rate_range",
        ),
        CheckConstraint(
            "stability_score >= 0.0 AND stability_score <= 1.0",
            name="check_stability_score_range",
        ),
        CheckConstraint(
            "learning_source IN ('explicit_feedback', 'behavioral_analysis', 'pattern_detection', 'manual_override')",
            name="check_learning_source",
        ),
    )

    def __repr__(self) -> str:
        return f"<UserPreference(id={self.id}, category={self.preference_category}, key='{self.preference_key}')>"

class UserBehaviorPattern(Base):
    """User behavioral patterns for learning and adaptation.

    Tracks user interaction patterns, engagement metrics, and behavioral
    data to improve preference learning and personalization.
    """

    __tablename__ = "user_behavior_patterns"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Pattern identification
    pattern_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type: activity_timing, topic_engagement, response_interaction, query_frequency",
    )
    pattern_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Descriptive name for the pattern"
    )
    pattern_data: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Pattern data including metrics, frequencies, and trends",
    )

    # Pattern metrics
    frequency_score: Mapped[float] = mapped_column(
        default=0.0, comment="How frequently this pattern occurs 0.0-1.0"
    )
    consistency_score: Mapped[float] = mapped_column(
        default=0.0, comment="How consistent this pattern is over time 0.0-1.0"
    )
    predictive_value: Mapped[float] = mapped_column(
        default=0.0, comment="How predictive this pattern is for preferences 0.0-1.0"
    )

    # Time window and validation
    observation_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="Start of observation period"
    )
    observation_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="End of observation period"
    )
    sample_size: Mapped[int] = mapped_column(
        nullable=False, comment="Number of data points used to identify pattern"
    )

    # Pattern lifecycle
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_validated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Whether pattern has been validated through user feedback",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="behavior_patterns")
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="user_behavior_patterns"
    )

    # Constraints
    __table_args__ = (
        Index("idx_user_behavior_patterns_user_type", "user_id", "pattern_type"),
        Index("idx_user_behavior_patterns_frequency", "frequency_score"),
        Index("idx_user_behavior_patterns_predictive", "predictive_value"),
        Index("idx_user_behavior_patterns_active", "is_active"),
        CheckConstraint(
            "pattern_type IN ('activity_timing', 'topic_engagement', 'response_interaction', 'query_frequency')",
            name="check_pattern_type",
        ),
        CheckConstraint(
            "frequency_score >= 0.0 AND frequency_score <= 1.0",
            name="check_frequency_score_range",
        ),
        CheckConstraint(
            "consistency_score >= 0.0 AND consistency_score <= 1.0",
            name="check_consistency_score_range",
        ),
        CheckConstraint(
            "predictive_value >= 0.0 AND predictive_value <= 1.0",
            name="check_predictive_value_range",
        ),
        CheckConstraint(
            "observation_start <= observation_end",
            name="check_observation_period_order",
        ),
    )

    def __repr__(self) -> str:
        return f"<UserBehaviorPattern(id={self.id}, type={self.pattern_type}, name='{self.pattern_name}')>"

class PrivacyConsent(Base):
    """Privacy consent tracking for memory data.

    Tracks user consent for different types of memory processing,
    data sharing, and retention policies with GDPR compliance.
    """

    __tablename__ = "privacy_consents"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Consent details
    consent_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type: memory_storage, preference_learning, team_sharing, analytics, data_export",
    )
    consent_scope: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Scope of consent: personal_memory, team_memory, cross_team, external_sharing",
    )
    consent_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Status: granted, withdrawn, expired, pending",
    )

    # Legal basis and processing purpose
    legal_basis: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="GDPR legal basis: consent, contract, legal_obligation, vital_interests, public_task, legitimate_interests",
    )
    processing_purpose: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Purpose of data processing"
    )

    # Consent metadata
    consent_version: Mapped[str] = mapped_column(
        String(20), default="1.0", comment="Version of consent terms"
    )
    consent_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="How consent was obtained: explicit, implicit, inherited, imported",
    )
    consent_evidence: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, comment="Evidence of consent including timestamps, IP, user agent"
    )

    # Expiration and renewal
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="When consent expires (if applicable)"
    )
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="When consent was withdrawn"
    )
    last_confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="Last time user confirmed consent"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="privacy_consents")
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="privacy_consents"
    )

    # Constraints
    __table_args__ = (
        Index("idx_privacy_consents_user_type", "user_id", "consent_type"),
        Index("idx_privacy_consents_status", "consent_status"),
        Index("idx_privacy_consents_expires", "expires_at"),
        Index("idx_privacy_consents_scope", "consent_scope"),
        UniqueConstraint(
            "user_id", "consent_type", "consent_scope", name="uq_user_consent"
        ),
        CheckConstraint(
            "consent_type IN ('memory_storage', 'preference_learning', 'team_sharing', 'analytics', 'data_export')",
            name="check_consent_type",
        ),
        CheckConstraint(
            "consent_status IN ('granted', 'withdrawn', 'expired', 'pending')",
            name="check_consent_status",
        ),
        CheckConstraint(
            "legal_basis IN ('consent', 'contract', 'legal_obligation', 'vital_interests', 'public_task', 'legitimate_interests')",
            name="check_legal_basis",
        ),
        CheckConstraint(
            "consent_method IN ('explicit', 'implicit', 'inherited', 'imported')",
            name="check_consent_method",
        ),
    )

    def __repr__(self) -> str:
        return f"<PrivacyConsent(id={self.id}, type={self.consent_type}, status={self.consent_status})>"

class DataRetentionPolicy(Base):
    """Data retention policies for different types of memory data.

    Defines how long different types of memory data should be retained
    and when they should be automatically archived or deleted.
    """

    __tablename__ = "data_retention_policies"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        comment="User-specific policy (null for organization default)",
    )
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Policy details
    data_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Category: conversations, decisions, user_memories, team_memories, preferences",
    )
    retention_period_days: Mapped[int] = mapped_column(
        nullable=False, comment="Number of days to retain data (0 = indefinite)"
    )
    archive_after_days: Mapped[Optional[int]] = mapped_column(
        comment="Days after which to archive data (optional)"
    )

    # Policy actions
    action_on_expiry: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Action: delete, archive, anonymize, prompt_user",
    )
    notification_days_before: Mapped[Optional[int]] = mapped_column(
        comment="Days before expiry to notify user"
    )

    # Policy metadata
    policy_source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Source: user_preference, organization_default, legal_requirement, system_default",
    )
    compliance_requirements: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, comment="List of compliance frameworks this policy satisfies"
    )

    # Status and validation
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_overridable: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Whether users can override this policy"
    )

    # Timestamps
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    effective_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="When this policy expires"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="retention_policies"
    )
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="retention_policies"
    )

    # Constraints
    __table_args__ = (
        Index("idx_retention_policies_user_category", "user_id", "data_category"),
        Index("idx_retention_policies_active", "is_active"),
        Index("idx_retention_policies_effective", "effective_from", "effective_until"),
        CheckConstraint(
            "data_category IN ('conversations', 'decisions', 'user_memories', 'team_memories', 'preferences')",
            name="check_data_category",
        ),
        CheckConstraint(
            "action_on_expiry IN ('delete', 'archive', 'anonymize', 'prompt_user')",
            name="check_action_on_expiry",
        ),
        CheckConstraint(
            "policy_source IN ('user_preference', 'organization_default', 'legal_requirement', 'system_default')",
            name="check_policy_source",
        ),
        CheckConstraint(
            "retention_period_days >= 0", name="check_retention_period_positive"
        ),
    )

    def __repr__(self) -> str:
        return f"<DataRetentionPolicy(id={self.id}, category={self.data_category}, days={self.retention_period_days})>"

class DataExportRequest(Base):
    """Data export requests for GDPR compliance and portability.

    Tracks user requests for data exports, ensuring compliance
    with data portability rights and providing audit trails.
    """

    __tablename__ = "data_export_requests"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Export request details
    export_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type: full_export, partial_export, specific_data, gdpr_export",
    )
    data_categories: Mapped[List[str]] = mapped_column(
        JSONB, nullable=False, comment="Categories of data to export"
    )
    export_format: Mapped[str] = mapped_column(
        String(20), default="json", comment="Format: json, csv, xml, pdf"
    )

    # Date range and filters
    date_range_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="Start date for data export (null = all time)"
    )
    date_range_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="End date for data export (null = until now)"
    )
    additional_filters: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, comment="Additional filters for data export"
    )

    # Request status and processing
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        comment="Status: pending, processing, completed, failed, expired",
    )
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Export results
    export_file_path: Mapped[Optional[str]] = mapped_column(
        String(500), comment="Path to generated export file"
    )
    export_file_size: Mapped[Optional[int]] = mapped_column(
        comment="Size of export file in bytes"
    )
    record_count: Mapped[Optional[int]] = mapped_column(
        comment="Number of records exported"
    )

    # Security and access
    download_token: Mapped[Optional[str]] = mapped_column(
        String(255), comment="Secure token for downloading export"
    )
    download_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="When download link expires"
    )
    download_count: Mapped[int] = mapped_column(
        default=0, comment="Number of times export was downloaded"
    )

    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, comment="Error message if export failed"
    )
    retry_count: Mapped[int] = mapped_column(
        default=0, comment="Number of retry attempts"
    )

    # Timestamps
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="data_export_requests")
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="data_export_requests"
    )

    # Constraints
    __table_args__ = (
        Index("idx_data_export_requests_user_status", "user_id", "status"),
        Index("idx_data_export_requests_requested", "requested_at"),
        Index("idx_data_export_requests_expires", "download_expires_at"),
        CheckConstraint(
            "export_type IN ('full_export', 'partial_export', 'specific_data', 'gdpr_export')",
            name="check_export_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed', 'expired')",
            name="check_export_status",
        ),
        CheckConstraint(
            "export_format IN ('json', 'csv', 'xml', 'pdf')", name="check_export_format"
        ),
        CheckConstraint(
            "date_range_start IS NULL OR date_range_end IS NULL OR date_range_start <= date_range_end",
            name="check_date_range_order",
        ),
    )

    def __repr__(self) -> str:
        return f"<DataExportRequest(id={self.id}, type={self.export_type}, status={self.status})>"

class MemoryEmbedding(Base):
    """Vector embeddings for semantic search of memories.

    Stores vector representations of memories for semantic search
    and similarity matching.
    """

    __tablename__ = "memory_embeddings"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_memory_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("user_memories.id", ondelete="CASCADE"),
        nullable=True,
    )
    team_memory_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("team_memories.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Embedding data
    embedding_model: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Model used to generate embedding"
    )
    embedding_version: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Version of the embedding model"
    )
    content_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="Hash of content for change detection"
    )

    # Vector storage reference (actual vectors stored in Weaviate/Pinecone)
    vector_id: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Reference ID in vector database"
    )
    vector_database: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Vector database used: weaviate, pinecone"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user_memory: Mapped[Optional["UserMemory"]] = relationship(
        "UserMemory", back_populates="embeddings"
    )
    team_memory: Mapped[Optional["TeamMemory"]] = relationship(
        "TeamMemory", back_populates="embeddings"
    )

    # Constraints
    __table_args__ = (
        Index("idx_memory_embeddings_user_memory", "user_memory_id"),
        Index("idx_memory_embeddings_team_memory", "team_memory_id"),
        Index("idx_memory_embeddings_vector", "vector_id"),
        Index("idx_memory_embeddings_model", "embedding_model", "embedding_version"),
        CheckConstraint(
            "(user_memory_id IS NOT NULL AND team_memory_id IS NULL) OR "
            "(user_memory_id IS NULL AND team_memory_id IS NOT NULL)",
            name="check_memory_embedding_reference",
        ),
        CheckConstraint(
            "vector_database IN ('weaviate', 'pinecone')", name="check_vector_database"
        ),
    )

    def __repr__(self) -> str:
        return f"<MemoryEmbedding(id={self.id}, model={self.embedding_model}, db={self.vector_database})>"
