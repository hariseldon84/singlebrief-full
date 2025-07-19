"""Memory Engine database models for SingleBrief.

This module contains all database models related to the Memory Engine system,
including conversations, decisions, user memories, and team memories.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, JSON,
    ForeignKey, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Conversation(Base):
    """Stores conversation history for team leads and AI interactions.
    
    This model tracks all conversations between users and the AI system,
    providing context for future interactions and memory building.
    """
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    team_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True
    )
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Conversation metadata
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    context_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Type of conversation: daily_brief, ad_hoc_query, team_interrogation"
    )
    session_id: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Privacy and consent
    is_shared_with_team: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    retention_policy: Mapped[str] = mapped_column(
        String(50), 
        default="standard",
        comment="Retention policy: standard, extended, permanent, delete_on_request"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="conversations")
    team: Mapped[Optional["Team"]] = relationship("Team", back_populates="conversations")
    organization: Mapped["Organization"] = relationship("Organization", back_populates="conversations")
    messages: Mapped[List["ConversationMessage"]] = relationship(
        "ConversationMessage", 
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.created_at"
    )
    decisions: Mapped[List["Decision"]] = relationship(
        "Decision", 
        back_populates="conversation",
        cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        Index("idx_conversations_user_created", "user_id", "created_at"),
        Index("idx_conversations_team_created", "team_id", "created_at"),
        Index("idx_conversations_context_type", "context_type"),
        Index("idx_conversations_session", "session_id"),
        CheckConstraint(
            "context_type IN ('daily_brief', 'ad_hoc_query', 'team_interrogation', 'memory_query')",
            name="check_conversation_context_type"
        ),
        CheckConstraint(
            "retention_policy IN ('standard', 'extended', 'permanent', 'delete_on_request')",
            name="check_retention_policy"
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
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    conversation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Message content
    message_type: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        comment="Type: user_query, ai_response, system_message"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="Additional metadata like response time, confidence scores, etc."
    )
    
    # AI-specific fields
    ai_model_used: Mapped[Optional[str]] = mapped_column(String(100))
    confidence_score: Mapped[Optional[float]] = mapped_column()
    sources_used: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB,
        comment="Sources and data used to generate response"
    )
    processing_time_ms: Mapped[Optional[int]] = mapped_column()
    
    # Message ordering and timing
    sequence_number: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")

    # Constraints
    __table_args__ = (
        Index("idx_conversation_messages_conv_seq", "conversation_id", "sequence_number"),
        Index("idx_conversation_messages_created", "created_at"),
        UniqueConstraint("conversation_id", "sequence_number", name="uq_conversation_message_sequence"),
        CheckConstraint(
            "message_type IN ('user_query', 'ai_response', 'system_message')",
            name="check_message_type"
        ),
        CheckConstraint(
            "confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)",
            name="check_confidence_score_range"
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
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    conversation_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    team_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True
    )
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Decision content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    decision_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Type: strategic, operational, personnel, technical, process"
    )
    priority_level: Mapped[str] = mapped_column(
        String(20), 
        default="medium",
        comment="Priority: low, medium, high, critical"
    )
    
    # Decision status and outcomes
    status: Mapped[str] = mapped_column(
        String(20), 
        default="pending",
        comment="Status: pending, approved, implemented, cancelled, reviewed"
    )
    outcome: Mapped[Optional[str]] = mapped_column(Text)
    impact_assessment: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="Assessment of decision impact and results"
    )
    
    # Stakeholders and context
    stakeholders: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        comment="List of user IDs affected by this decision"
    )
    context_tags: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        comment="Tags for categorization and search"
    )
    
    # Timing
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    implementation_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    implemented_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

    # Relationships
    conversation: Mapped[Optional["Conversation"]] = relationship("Conversation", back_populates="decisions")
    user: Mapped["User"] = relationship("User", back_populates="decisions")
    team: Mapped[Optional["Team"]] = relationship("Team", back_populates="decisions")
    organization: Mapped["Organization"] = relationship("Organization", back_populates="decisions")

    # Constraints
    __table_args__ = (
        Index("idx_decisions_user_decided", "user_id", "decided_at"),
        Index("idx_decisions_team_decided", "team_id", "decided_at"),
        Index("idx_decisions_status", "status"),
        Index("idx_decisions_type", "decision_type"),
        Index("idx_decisions_priority", "priority_level"),
        CheckConstraint(
            "decision_type IN ('strategic', 'operational', 'personnel', 'technical', 'process')",
            name="check_decision_type"
        ),
        CheckConstraint(
            "priority_level IN ('low', 'medium', 'high', 'critical')",
            name="check_priority_level"
        ),
        CheckConstraint(
            "status IN ('pending', 'approved', 'implemented', 'cancelled', 'reviewed')",
            name="check_decision_status"
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
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Memory content
    memory_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Type: preference, behavior_pattern, context, personal_info, work_style"
    )
    category: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="Category for organizing memories"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="Additional structured data and context"
    )
    
    # Memory properties
    importance_score: Mapped[float] = mapped_column(
        default=0.5,
        comment="Importance score 0.0-1.0 for memory prioritization"
    )
    confidence_level: Mapped[float] = mapped_column(
        default=0.5,
        comment="Confidence in memory accuracy 0.0-1.0"
    )
    source: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="Source: conversation, explicit_input, inferred, external_integration"
    )
    
    # Privacy and sharing
    is_private: Mapped[bool] = mapped_column(
        Boolean, 
        default=True,
        comment="Whether memory is private to user or can be shared"
    )
    sharing_level: Mapped[str] = mapped_column(
        String(20), 
        default="private",
        comment="Sharing level: private, team, organization"
    )
    
    # Memory lifecycle
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    access_count: Mapped[int] = mapped_column(default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_memories")
    organization: Mapped["Organization"] = relationship("Organization", back_populates="user_memories")
    embeddings: Mapped[List["MemoryEmbedding"]] = relationship(
        "MemoryEmbedding", 
        back_populates="user_memory",
        cascade="all, delete-orphan"
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
            name="check_user_memory_type"
        ),
        CheckConstraint(
            "importance_score >= 0.0 AND importance_score <= 1.0",
            name="check_importance_score_range"
        ),
        CheckConstraint(
            "confidence_level >= 0.0 AND confidence_level <= 1.0",
            name="check_confidence_level_range"
        ),
        CheckConstraint(
            "sharing_level IN ('private', 'team', 'organization')",
            name="check_sharing_level"
        ),
        CheckConstraint(
            "source IN ('conversation', 'explicit_input', 'inferred', 'external_integration')",
            name="check_memory_source"
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
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    team_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False
    )
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )
    created_by_user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Memory content
    memory_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Type: team_process, decision_pattern, collaboration_style, project_context"
    )
    category: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="Category for organizing team memories"
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="Additional structured data and context"
    )
    
    # Memory properties
    importance_score: Mapped[float] = mapped_column(
        default=0.5,
        comment="Importance score 0.0-1.0 for memory prioritization"
    )
    relevance_score: Mapped[float] = mapped_column(
        default=0.5,
        comment="Current relevance score 0.0-1.0"
    )
    source: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="Source: team_discussion, decision, process_observation, external_input"
    )
    
    # Team consensus and validation
    consensus_level: Mapped[float] = mapped_column(
        default=0.5,
        comment="Team consensus on memory accuracy 0.0-1.0"
    )
    validated_by_members: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        comment="List of user IDs who have validated this memory"
    )
    
    # Visibility and access
    visibility: Mapped[str] = mapped_column(
        String(20), 
        default="team",
        comment="Visibility: team, organization, private"
    )
    access_level: Mapped[str] = mapped_column(
        String(20), 
        default="read_write",
        comment="Access level: read_only, read_write, admin_only"
    )
    
    # Memory lifecycle
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    access_count: Mapped[int] = mapped_column(default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

    # Relationships
    team: Mapped["Team"] = relationship("Team", back_populates="team_memories")
    organization: Mapped["Organization"] = relationship("Organization", back_populates="team_memories")
    created_by: Mapped["User"] = relationship("User", back_populates="created_team_memories")
    embeddings: Mapped[List["MemoryEmbedding"]] = relationship(
        "MemoryEmbedding", 
        back_populates="team_memory",
        cascade="all, delete-orphan"
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
            name="check_team_memory_type"
        ),
        CheckConstraint(
            "importance_score >= 0.0 AND importance_score <= 1.0",
            name="check_team_importance_score_range"
        ),
        CheckConstraint(
            "relevance_score >= 0.0 AND relevance_score <= 1.0",
            name="check_relevance_score_range"
        ),
        CheckConstraint(
            "consensus_level >= 0.0 AND consensus_level <= 1.0",
            name="check_consensus_level_range"
        ),
        CheckConstraint(
            "visibility IN ('team', 'organization', 'private')",
            name="check_team_memory_visibility"
        ),
        CheckConstraint(
            "access_level IN ('read_only', 'read_write', 'admin_only')",
            name="check_team_memory_access_level"
        ),
        CheckConstraint(
            "source IN ('team_discussion', 'decision', 'process_observation', 'external_input')",
            name="check_team_memory_source"
        ),
    )

    def __repr__(self) -> str:
        return f"<TeamMemory(id={self.id}, title='{self.title}', team_id={self.team_id})>"


class MemoryEmbedding(Base):
    """Vector embeddings for semantic search of memories.
    
    Stores vector representations of memories for semantic search
    and similarity matching.
    """
    __tablename__ = "memory_embeddings"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    user_memory_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("user_memories.id", ondelete="CASCADE"),
        nullable=True
    )
    team_memory_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("team_memories.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # Embedding data
    embedding_model: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="Model used to generate embedding"
    )
    embedding_version: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        comment="Version of the embedding model"
    )
    content_hash: Mapped[str] = mapped_column(
        String(64), 
        nullable=False,
        comment="Hash of content for change detection"
    )
    
    # Vector storage reference (actual vectors stored in Weaviate/Pinecone)
    vector_id: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        comment="Reference ID in vector database"
    )
    vector_database: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Vector database used: weaviate, pinecone"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

    # Relationships
    user_memory: Mapped[Optional["UserMemory"]] = relationship("UserMemory", back_populates="embeddings")
    team_memory: Mapped[Optional["TeamMemory"]] = relationship("TeamMemory", back_populates="embeddings")

    # Constraints
    __table_args__ = (
        Index("idx_memory_embeddings_user_memory", "user_memory_id"),
        Index("idx_memory_embeddings_team_memory", "team_memory_id"),
        Index("idx_memory_embeddings_vector", "vector_id"),
        Index("idx_memory_embeddings_model", "embedding_model", "embedding_version"),
        CheckConstraint(
            "(user_memory_id IS NOT NULL AND team_memory_id IS NULL) OR "
            "(user_memory_id IS NULL AND team_memory_id IS NOT NULL)",
            name="check_memory_embedding_reference"
        ),
        CheckConstraint(
            "vector_database IN ('weaviate', 'pinecone')",
            name="check_vector_database"
        ),
    )

    def __repr__(self) -> str:
        return f"<MemoryEmbedding(id={self.id}, model={self.embedding_model}, db={self.vector_database})>"