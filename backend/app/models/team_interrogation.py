"""
Team Interrogation AI Models

Database models for the Team Interrogation AI system including:
- Question generation and management
- Response collection and tracking
- Communication style and preferences
- Team insights and analytics
- Feedback and continuous improvement
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, ForeignKey,
                        Index, Integer, String, Text)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base

class QuestionType(str, Enum):
    """Types of questions that can be generated"""

    MULTIPLE_CHOICE = "multiple_choice"
    OPEN_ENDED = "open_ended"
    SCALE = "scale"
    YES_NO = "yes_no"
    RANKING = "ranking"
    FOLLOW_UP = "follow_up"

class QuestionComplexity(str, Enum):
    """Complexity levels for questions"""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    TECHNICAL = "technical"

class ResponseStatus(str, Enum):
    """Status of question responses"""

    PENDING = "pending"
    PARTIAL = "partial"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    EXPIRED = "expired"

class CommunicationStyle(str, Enum):
    """Communication styles for team interactions"""

    FORMAL = "formal"
    CASUAL = "casual"
    DIRECT = "direct"
    DIPLOMATIC = "diplomatic"
    TECHNICAL = "technical"
    SUPPORTIVE = "supportive"

class TrustLevel(str, Enum):
    """Trust levels between AI and team members"""

    LOW = "low"
    BUILDING = "building"
    MODERATE = "moderate"
    HIGH = "high"
    EXCELLENT = "excellent"

class QuestionTemplate(Base):
    """Template library for question generation"""

    __tablename__ = "question_templates"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    question_type: Mapped[QuestionType] = mapped_column(String(50), nullable=False)
    complexity: Mapped[QuestionComplexity] = mapped_column(String(50), nullable=False)

    # Template content
    template_text: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    options: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON
    )  # For multiple choice, scales

    # Targeting and effectiveness
    target_roles: Mapped[List[str]] = mapped_column(JSON, default=list)
    effectiveness_score: Mapped[float] = mapped_column(Float, default=0.0)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(36))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    questions = relationship("GeneratedQuestion", back_populates="template")

    __table_args__ = (
        Index("idx_question_template_category_type", "category", "question_type"),
        Index("idx_question_template_effectiveness", "effectiveness_score"),
    )

class TeamMemberProfile(Base):
    """Profile information for team members for personalized questioning"""

    __tablename__ = "team_member_profiles"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False
    )
    team_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False, index=True)

    # Role and expertise
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    seniority_level: Mapped[str] = mapped_column(String(50), nullable=False)
    expertise_areas: Mapped[List[str]] = mapped_column(JSON, default=list)
    knowledge_domains: Mapped[Dict[str, float]] = mapped_column(
        JSON, default=dict
    )  # domain -> confidence score

    # Communication preferences
    preferred_style: Mapped[CommunicationStyle] = mapped_column(
        String(50), default=CommunicationStyle.CASUAL
    )
    formality_preference: Mapped[float] = mapped_column(
        Float, default=0.5
    )  # 0.0 = casual, 1.0 = formal
    preferred_channels: Mapped[List[str]] = mapped_column(JSON, default=list)

    # Availability and workload
    typical_availability: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict
    )  # schedule patterns
    current_workload: Mapped[float] = mapped_column(
        Float, default=0.5
    )  # 0.0 = light, 1.0 = heavy
    response_time_preference: Mapped[int] = mapped_column(Integer, default=24)  # hours

    # Interaction history
    total_questions_received: Mapped[int] = mapped_column(Integer, default=0)
    response_rate: Mapped[float] = mapped_column(Float, default=0.0)
    avg_response_time: Mapped[float] = mapped_column(Float, default=0.0)  # hours
    trust_level: Mapped[TrustLevel] = mapped_column(
        String(50), default=TrustLevel.BUILDING
    )

    # Cultural and personal
    cultural_context: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    communication_notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="team_profile")
    questions_received = relationship(
        "GeneratedQuestion",
        foreign_keys="GeneratedQuestion.recipient_id",
        back_populates="recipient",
    )
    responses = relationship("QuestionResponse", back_populates="responder")

    __table_args__ = (
        Index("idx_team_member_team_role", "team_id", "role"),
        Index("idx_team_member_response_rate", "response_rate"),
    )

class GeneratedQuestion(Base):
    """Individual questions generated by the AI for team members"""

    __tablename__ = "generated_questions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    template_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("question_templates.id")
    )
    recipient_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("team_member_profiles.id"), nullable=False
    )

    # Question content
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(String(50), nullable=False)
    complexity: Mapped[QuestionComplexity] = mapped_column(String(50), nullable=False)
    options: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON
    )  # For multiple choice, scales

    # Context and targeting
    context: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict
    )  # Project, timing, etc.
    reasoning: Mapped[Optional[str]] = mapped_column(
        Text
    )  # Why this question was generated
    priority: Mapped[float] = mapped_column(Float, default=0.5)

    # Delivery and timing
    delivery_channel: Mapped[str] = mapped_column(String(50), nullable=False)
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Follow-up chain
    parent_question_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("generated_questions.id")
    )
    follow_up_trigger: Mapped[Optional[str]] = mapped_column(
        Text
    )  # Conditions for follow-up

    # Quality and effectiveness
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    effectiveness_score: Mapped[Optional[float]] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    template = relationship("QuestionTemplate", back_populates="questions")
    recipient = relationship(
        "TeamMemberProfile",
        foreign_keys=[recipient_id],
        back_populates="questions_received",
    )
    responses = relationship("QuestionResponse", back_populates="question")
    follow_ups = relationship("GeneratedQuestion", remote_side=[parent_question_id])
    parent = relationship("GeneratedQuestion", remote_side=[id], overlaps="follow_ups")

    __table_args__ = (
        Index("idx_generated_question_recipient_status", "recipient_id", "sent_at"),
        Index("idx_generated_question_scheduled", "scheduled_for"),
    )

class QuestionResponse(Base):
    """Responses to generated questions from team members"""

    __tablename__ = "question_responses"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    question_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("generated_questions.id"), nullable=False
    )
    responder_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("team_member_profiles.id"), nullable=False
    )

    # Response content
    response_text: Mapped[Optional[str]] = mapped_column(Text)
    selected_options: Mapped[Optional[List[str]]] = mapped_column(
        JSON
    )  # For multiple choice
    scale_value: Mapped[Optional[float]] = mapped_column(Float)  # For scale questions

    # Response metadata
    status: Mapped[ResponseStatus] = mapped_column(
        String(50), default=ResponseStatus.PENDING
    )
    confidence: Mapped[Optional[float]] = mapped_column(
        Float
    )  # Responder's confidence in answer
    response_channel: Mapped[str] = mapped_column(String(50), nullable=False)

    # Timing and engagement
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    response_time_seconds: Mapped[Optional[int]] = mapped_column(Integer)

    # Quality and sentiment
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float)  # -1.0 to 1.0
    quality_indicators: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    follow_up_needed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Anonymous/confidential handling
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    is_confidential: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    question = relationship("GeneratedQuestion", back_populates="responses")
    responder = relationship("TeamMemberProfile", back_populates="responses")

    __table_args__ = (
        Index("idx_question_response_status", "status"),
        Index("idx_question_response_completed", "completed_at"),
    )

class TeamInsight(Base):
    """Synthesized insights from team responses"""

    __tablename__ = "team_insights"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    team_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Insight content
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    detailed_analysis: Mapped[str] = mapped_column(Text, nullable=False)
    key_themes: Mapped[List[str]] = mapped_column(JSON, default=list)

    # Source information
    source_questions: Mapped[List[str]] = mapped_column(
        JSON, default=list
    )  # Question IDs
    source_responses: Mapped[List[str]] = mapped_column(
        JSON, default=list
    )  # Response IDs
    response_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Analysis metrics
    consensus_level: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # 0.0 = high disagreement, 1.0 = consensus
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)  # -1.0 to 1.0
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Actionable recommendations
    recommendations: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    priority_level: Mapped[str] = mapped_column(String(50), default="medium")

    # Trend and pattern analysis
    trend_indicators: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    pattern_type: Mapped[Optional[str]] = mapped_column(String(100))

    # Conflicts and concerns
    identified_conflicts: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON, default=list
    )
    risk_indicators: Mapped[List[str]] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("idx_team_insight_team_created", "team_id", "created_at"),
        Index("idx_team_insight_confidence", "confidence_score"),
    )

class InteractionFeedback(Base):
    """Feedback on AI interactions for continuous improvement"""

    __tablename__ = "interaction_feedback"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    question_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("generated_questions.id")
    )
    responder_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("team_member_profiles.id"), nullable=False
    )

    # Feedback content
    interaction_rating: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # 1-5 scale
    question_relevance: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5 scale
    question_clarity: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5 scale
    timing_appropriateness: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5 scale

    # Communication feedback
    tone_rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5 scale
    formality_preference: Mapped[Optional[str]] = mapped_column(String(50))
    communication_improvements: Mapped[Optional[str]] = mapped_column(Text)

    # Trust and rapport
    trust_change: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # increased, decreased, unchanged
    rapport_rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5 scale
    intrusion_level: Mapped[Optional[int]] = mapped_column(
        Integer
    )  # 1-5 scale (5 = very intrusive)

    # Usefulness and value
    response_usefulness: Mapped[Optional[int]] = mapped_column(
        Integer
    )  # 1-5 scale (for leaders)
    would_recommend: Mapped[Optional[bool]] = mapped_column(Boolean)

    # Improvement suggestions
    suggestions: Mapped[Optional[str]] = mapped_column(Text)
    preferred_alternatives: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Implicit feedback indicators
    response_time_satisfaction: Mapped[Optional[float]] = mapped_column(Float)
    engagement_indicators: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    question = relationship("GeneratedQuestion")
    responder = relationship("TeamMemberProfile")

    __table_args__ = (
        Index("idx_interaction_feedback_rating", "interaction_rating"),
        Index("idx_interaction_feedback_created", "created_at"),
    )

class CommunicationPattern(Base):
    """Learned communication patterns for different team members"""

    __tablename__ = "communication_patterns"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    profile_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("team_member_profiles.id"), nullable=False
    )

    # Pattern identification
    pattern_name: Mapped[str] = mapped_column(String(100), nullable=False)
    pattern_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # tone, timing, format, etc.

    # Pattern parameters
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    effectiveness_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_level: Mapped[float] = mapped_column(Float, default=0.0)

    # Learning metadata
    learned_from_interactions: Mapped[int] = mapped_column(Integer, default=0)
    last_reinforcement: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # Application rules
    conditions: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    profile = relationship("TeamMemberProfile")

    __table_args__ = (
        Index("idx_communication_pattern_effectiveness", "effectiveness_score"),
        Index("idx_communication_pattern_type", "pattern_type"),
    )
