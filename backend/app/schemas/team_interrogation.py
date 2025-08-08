"""
Team Interrogation API Schemas

Pydantic schemas for request/response validation in the Team Interrogation AI API
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator

from ..models.team_interrogation import (CommunicationStyle,
                                         QuestionComplexity, QuestionType,
                                         ResponseStatus, TrustLevel)

# Question Template Schemas

class QuestionTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: str = Field(..., min_length=1, max_length=100)
    question_type: QuestionType
    complexity: QuestionComplexity
    template_text: str = Field(..., min_length=1)
    variables: Dict[str, Any] = Field(default_factory=dict)
    options: Optional[Dict[str, Any]] = None
    target_roles: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

class QuestionTemplateCreate(QuestionTemplateBase):
    pass

class QuestionTemplateResponse(QuestionTemplateBase):
    id: str
    effectiveness_score: float
    usage_count: int
    is_active: bool
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Team Member Profile Schemas

class TeamMemberProfileBase(BaseModel):
    user_id: str = Field(..., min_length=1)
    team_id: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1, max_length=100)
    seniority_level: str = Field(..., min_length=1, max_length=50)
    expertise_areas: List[str] = Field(default_factory=list)
    knowledge_domains: Dict[str, float] = Field(default_factory=dict)
    preferred_style: CommunicationStyle = CommunicationStyle.CASUAL
    formality_preference: float = Field(default=0.5, ge=0.0, le=1.0)
    preferred_channels: List[str] = Field(default_factory=list)
    typical_availability: Dict[str, Any] = Field(default_factory=dict)
    current_workload: float = Field(default=0.5, ge=0.0, le=1.0)
    response_time_preference: int = Field(default=24, gt=0)
    cultural_context: Optional[Dict[str, Any]] = None
    communication_notes: Optional[str] = None

    @field_validator("formality_preference")
    @classmethod
    def validate_formality_preference(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Formality preference must be between 0.0 and 1.0")
        return v

    @field_validator("current_workload")
    @classmethod
    def validate_current_workload(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Current workload must be between 0.0 and 1.0")
        return v

class TeamMemberProfileCreate(TeamMemberProfileBase):
    pass

class TeamMemberProfileUpdate(BaseModel):
    role: Optional[str] = Field(None, min_length=1, max_length=100)
    seniority_level: Optional[str] = Field(None, min_length=1, max_length=50)
    expertise_areas: Optional[List[str]] = None
    knowledge_domains: Optional[Dict[str, float]] = None
    preferred_style: Optional[CommunicationStyle] = None
    formality_preference: Optional[float] = Field(None, ge=0.0, le=1.0)
    preferred_channels: Optional[List[str]] = None
    typical_availability: Optional[Dict[str, Any]] = None
    current_workload: Optional[float] = Field(None, ge=0.0, le=1.0)
    response_time_preference: Optional[int] = Field(None, gt=0)
    cultural_context: Optional[Dict[str, Any]] = None
    communication_notes: Optional[str] = None

class TeamMemberProfileResponse(TeamMemberProfileBase):
    id: str
    total_questions_received: int
    response_rate: float
    avg_response_time: float
    trust_level: TrustLevel
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Generated Question Schemas

class QuestionGenerationRequest(BaseModel):
    recipient_id: str = Field(..., min_length=1)
    context: Dict[str, Any] = Field(default_factory=dict)
    target_complexity: Optional[QuestionComplexity] = None
    question_type: Optional[QuestionType] = None

class BatchQuestionRequest(BaseModel):
    team_id: str = Field(..., min_length=1)
    context: Dict[str, Any] = Field(default_factory=dict)
    max_questions: int = Field(default=10, gt=0, le=50)

class GeneratedQuestionResponse(BaseModel):
    id: str
    template_id: Optional[str]
    recipient_id: str
    question_text: str
    question_type: QuestionType
    complexity: QuestionComplexity
    options: Optional[Dict[str, Any]]
    context: Dict[str, Any]
    reasoning: Optional[str]
    priority: float
    delivery_channel: str
    scheduled_for: Optional[datetime]
    sent_at: Optional[datetime]
    expires_at: Optional[datetime]
    parent_question_id: Optional[str]
    follow_up_trigger: Optional[str]
    quality_score: float
    effectiveness_score: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Question Response Schemas

class QuestionResponseBase(BaseModel):
    question_id: str = Field(..., min_length=1)
    responder_id: str = Field(..., min_length=1)
    response_text: Optional[str] = None
    selected_options: Optional[List[str]] = None
    scale_value: Optional[float] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    response_channel: str = Field(..., min_length=1)
    is_anonymous: bool = False
    is_confidential: bool = False

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v):
        if v is not None and not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v

class QuestionResponseCreate(QuestionResponseBase):
    status: ResponseStatus = ResponseStatus.COMPLETED
    started_at: Optional[datetime] = None
    response_time_seconds: Optional[int] = Field(None, gt=0)

class QuestionResponseResponse(QuestionResponseBase):
    id: str
    status: ResponseStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    response_time_seconds: Optional[int]
    sentiment_score: Optional[float]
    quality_indicators: Dict[str, Any]
    follow_up_needed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Team Insight Schemas

class TeamInsightResponse(BaseModel):
    id: str
    team_id: str
    title: str
    summary: str
    detailed_analysis: str
    key_themes: List[str]
    source_questions: List[str]
    source_responses: List[str]
    response_count: int
    consensus_level: float
    sentiment_score: float
    confidence_score: float
    recommendations: List[Dict[str, Any]]
    priority_level: str
    trend_indicators: Dict[str, Any]
    pattern_type: Optional[str]
    identified_conflicts: List[Dict[str, Any]]
    risk_indicators: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Interaction Feedback Schemas

class InteractionFeedbackBase(BaseModel):
    question_id: Optional[str] = None
    responder_id: str = Field(..., min_length=1)
    interaction_rating: int = Field(..., ge=1, le=5)
    question_relevance: Optional[int] = Field(None, ge=1, le=5)
    question_clarity: Optional[int] = Field(None, ge=1, le=5)
    timing_appropriateness: Optional[int] = Field(None, ge=1, le=5)
    tone_rating: Optional[int] = Field(None, ge=1, le=5)
    formality_preference: Optional[str] = None
    communication_improvements: Optional[str] = None
    trust_change: Optional[str] = None
    rapport_rating: Optional[int] = Field(None, ge=1, le=5)
    intrusion_level: Optional[int] = Field(None, ge=1, le=5)
    response_usefulness: Optional[int] = Field(None, ge=1, le=5)
    would_recommend: Optional[bool] = None
    suggestions: Optional[str] = None
    preferred_alternatives: Optional[Dict[str, Any]] = None

class InteractionFeedbackCreate(InteractionFeedbackBase):
    response_time_satisfaction: Optional[float] = Field(None, ge=0.0, le=1.0)
    engagement_indicators: Dict[str, Any] = Field(default_factory=dict)

class InteractionFeedbackResponse(InteractionFeedbackBase):
    id: str
    response_time_satisfaction: Optional[float]
    engagement_indicators: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

# Communication Pattern Schemas

class CommunicationPatternResponse(BaseModel):
    id: str
    profile_id: str
    pattern_name: str
    pattern_type: str
    parameters: Dict[str, Any]
    effectiveness_score: float
    confidence_level: float
    learned_from_interactions: int
    last_reinforcement: datetime
    conditions: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Analytics Schemas

class TeamAnalyticsResponse(BaseModel):
    team_id: str
    period: Dict[str, Optional[datetime]]
    metrics: Dict[str, Union[int, float]]

class QuestionEffectivenessMetrics(BaseModel):
    template_id: Optional[str]
    question_type: QuestionType
    complexity: QuestionComplexity
    total_questions: int
    response_rate: float
    avg_quality_score: float
    avg_response_time: float
    effectiveness_trend: List[Dict[str, Any]]

class TeamMemberEngagementMetrics(BaseModel):
    profile_id: str
    user_id: str
    role: str
    questions_received: int
    responses_completed: int
    response_rate: float
    avg_response_time: float
    avg_feedback_rating: float
    trust_level: TrustLevel
    engagement_trend: List[Dict[str, Any]]

# Error Response Schema

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    suggestions: Optional[List[str]] = None
