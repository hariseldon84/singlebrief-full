"""
Team Interrogation API Endpoints

API endpoints for the Team Interrogation AI system including:
- Question generation and management
- Response collection and tracking
- Team insights and analytics
- Communication preferences
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ....core.auth import get_current_user
from ....core.database import get_db
from ....models.team_interrogation import (CommunicationPattern,
                                           CommunicationStyle,
                                           GeneratedQuestion,
                                           InteractionFeedback,
                                           QuestionComplexity,
                                           QuestionResponse, QuestionTemplate,
                                           QuestionType, ResponseStatus,
                                           TeamInsight, TeamMemberProfile)
from ....models.user import User
from ....schemas.team_interrogation import (BatchQuestionRequest,
                                            CommunicationPatternResponse,
                                            GeneratedQuestionResponse,
                                            InteractionFeedbackCreate,
                                            InteractionFeedbackResponse,
                                            QuestionGenerationRequest,
                                            QuestionResponseCreate,
                                            QuestionResponseResponse,
                                            QuestionTemplateCreate,
                                            QuestionTemplateResponse,
                                            TeamInsightResponse,
                                            TeamMemberProfileCreate,
                                            TeamMemberProfileResponse,
                                            TeamMemberProfileUpdate)
from ....services.communication_service import CommunicationService
from ....services.question_generation import QuestionGenerationService
from ....services.team_insight_service import TeamInsightService

router = APIRouter()

# Question Template Management
@router.post("/templates", response_model=QuestionTemplateResponse)
async def create_question_template(
    template_data: QuestionTemplateCreate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new question template"""

    question_service = QuestionGenerationService(db)

    template = await question_service.create_question_template(
        name=template_data.name,
        description=template_data.description,
        category=template_data.category,
        question_type=template_data.question_type,
        complexity=template_data.complexity,
        template_text=template_data.template_text,
        variables=template_data.variables,
        target_roles=template_data.target_roles,
        options=template_data.options,
        tags=template_data.tags,
    )

    return template

@router.get("/templates", response_model=List[QuestionTemplateResponse])
async def get_question_templates(
    category: Optional[str] = Query(None),
    question_type: Optional[QuestionType] = Query(None),
    complexity: Optional[QuestionComplexity] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get question templates with optional filtering"""

    query = db.query(QuestionTemplate).filter(QuestionTemplate.is_active == True)

    if category:
        query = query.filter(QuestionTemplate.category == category)
    if question_type:
        query = query.filter(QuestionTemplate.question_type == question_type)
    if complexity:
        query = query.filter(QuestionTemplate.complexity == complexity)

    templates = query.offset(skip).limit(limit).all()
    return templates

@router.get("/templates/{template_id}", response_model=QuestionTemplateResponse)
async def get_question_template(
    template_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get a specific question template"""

    template = (
        db.query(QuestionTemplate).filter(QuestionTemplate.id == template_id).first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Question template not found")

    return template

@router.put("/templates/{template_id}/optimize")
async def optimize_template_effectiveness(
    template_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Optimize template effectiveness based on usage data"""

    question_service = QuestionGenerationService(db)
    await question_service.optimize_question_effectiveness(template_id)

    return {"message": "Template optimization completed"}

# Team Member Profile Management
@router.post("/profiles", response_model=TeamMemberProfileResponse)
async def create_team_member_profile(
    profile_data: TeamMemberProfileCreate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new team member profile"""

    # Check if profile already exists
    existing_profile = (
        db.query(TeamMemberProfile)
        .filter(TeamMemberProfile.user_id == profile_data.user_id)
        .first()
    )

    if existing_profile:
        raise HTTPException(
            status_code=400, detail="Profile already exists for this user"
        )

    profile = TeamMemberProfile(**profile_data.dict())
    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile

@router.get("/profiles", response_model=List[TeamMemberProfileResponse])
async def get_team_member_profiles(
    team_id: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get team member profiles with optional filtering"""

    query = db.query(TeamMemberProfile)

    if team_id:
        query = query.filter(TeamMemberProfile.team_id == team_id)
    if role:
        query = query.filter(TeamMemberProfile.role == role)

    profiles = query.offset(skip).limit(limit).all()
    return profiles

@router.get("/profiles/{profile_id}", response_model=TeamMemberProfileResponse)
async def get_team_member_profile(
    profile_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get a specific team member profile"""

    profile = (
        db.query(TeamMemberProfile).filter(TeamMemberProfile.id == profile_id).first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Team member profile not found")

    return profile

@router.put("/profiles/{profile_id}", response_model=TeamMemberProfileResponse)
async def update_team_member_profile(
    profile_id: str,
    profile_update: TeamMemberProfileUpdate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Update a team member profile"""

    profile = (
        db.query(TeamMemberProfile).filter(TeamMemberProfile.id == profile_id).first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Team member profile not found")

    update_data = profile_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)

    return profile

# Question Generation
@router.post("/questions/generate", response_model=GeneratedQuestionResponse)
async def generate_question(
    request: QuestionGenerationRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Generate a question for a specific team member"""

    question_service = QuestionGenerationService(db)

    question = await question_service.generate_question_for_member(
        recipient_id=request.recipient_id,
        context=request.context,
        target_complexity=request.target_complexity,
        question_type=request.question_type,
    )

    return question

@router.post(
    "/questions/generate-batch", response_model=List[GeneratedQuestionResponse]
)
async def generate_batch_questions(
    request: BatchQuestionRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Generate questions for multiple team members"""

    question_service = QuestionGenerationService(db)

    questions = await question_service.generate_batch_questions(
        team_id=request.team_id,
        context=request.context,
        max_questions=request.max_questions,
    )

    return questions

@router.get("/questions", response_model=List[GeneratedQuestionResponse])
async def get_questions(
    recipient_id: Optional[str] = Query(None),
    team_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get generated questions with filtering"""

    query = db.query(GeneratedQuestion)

    if recipient_id:
        query = query.filter(GeneratedQuestion.recipient_id == recipient_id)

    if team_id:
        query = query.join(TeamMemberProfile).filter(
            TeamMemberProfile.team_id == team_id
        )

    if start_date:
        query = query.filter(GeneratedQuestion.created_at >= start_date)
    if end_date:
        query = query.filter(GeneratedQuestion.created_at <= end_date)

    questions = (
        query.order_by(GeneratedQuestion.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return questions

@router.get("/questions/{question_id}", response_model=GeneratedQuestionResponse)
async def get_question(
    question_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get a specific generated question"""

    question = (
        db.query(GeneratedQuestion).filter(GeneratedQuestion.id == question_id).first()
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    return question

@router.post(
    "/questions/{question_id}/follow-up", response_model=GeneratedQuestionResponse
)
async def generate_follow_up_question(
    question_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Generate a follow-up question based on the response to a previous question"""

    # Get the most recent response to this question
    response = (
        db.query(QuestionResponse)
        .filter(QuestionResponse.question_id == question_id)
        .order_by(QuestionResponse.created_at.desc())
        .first()
    )

    if not response:
        raise HTTPException(
            status_code=400, detail="No response found for this question"
        )

    question_service = QuestionGenerationService(db)
    follow_up = await question_service.generate_follow_up_question(
        question_id, response
    )

    if not follow_up:
        raise HTTPException(status_code=400, detail="No follow-up question needed")

    return follow_up

# Question Response Management
@router.post("/responses", response_model=QuestionResponseResponse)
async def create_question_response(
    response_data: QuestionResponseCreate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Create a response to a question"""

    # Verify question exists
    question = (
        db.query(GeneratedQuestion)
        .filter(GeneratedQuestion.id == response_data.question_id)
        .first()
    )

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Check if response already exists
    existing_response = (
        db.query(QuestionResponse)
        .filter(
            QuestionResponse.question_id == response_data.question_id,
            QuestionResponse.responder_id == response_data.responder_id,
        )
        .first()
    )

    if existing_response:
        # Update existing response
        update_data = response_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field != "question_id":  # Don't update question_id
                setattr(existing_response, field, value)

        existing_response.updated_at = datetime.utcnow()
        if response_data.status == ResponseStatus.COMPLETED:
            existing_response.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(existing_response)
        return existing_response

    # Create new response
    response = QuestionResponse(**response_data.dict())
    if response_data.status == ResponseStatus.COMPLETED:
        response.completed_at = datetime.utcnow()

    db.add(response)
    db.commit()
    db.refresh(response)

    return response

@router.get("/responses", response_model=List[QuestionResponseResponse])
async def get_question_responses(
    question_id: Optional[str] = Query(None),
    responder_id: Optional[str] = Query(None),
    status: Optional[ResponseStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get question responses with filtering"""

    query = db.query(QuestionResponse)

    if question_id:
        query = query.filter(QuestionResponse.question_id == question_id)
    if responder_id:
        query = query.filter(QuestionResponse.responder_id == responder_id)
    if status:
        query = query.filter(QuestionResponse.status == status)

    responses = (
        query.order_by(QuestionResponse.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return responses

# Team Insights
@router.get("/insights", response_model=List[TeamInsightResponse])
async def get_team_insights(
    team_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get team insights with filtering"""

    query = db.query(TeamInsight).filter(TeamInsight.team_id == team_id)

    if start_date:
        query = query.filter(TeamInsight.created_at >= start_date)
    if end_date:
        query = query.filter(TeamInsight.created_at <= end_date)

    insights = (
        query.order_by(TeamInsight.created_at.desc()).offset(skip).limit(limit).all()
    )
    return insights

@router.post("/insights/generate")
async def generate_team_insights(
    team_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Generate new insights from recent team responses"""

    insight_service = TeamInsightService(db)
    insights = await insight_service.generate_insights_for_team(team_id)

    return {"message": f"Generated {len(insights)} new insights"}

# Interaction Feedback
@router.post("/feedback", response_model=InteractionFeedbackResponse)
async def create_interaction_feedback(
    feedback_data: InteractionFeedbackCreate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Create feedback on an AI interaction"""

    feedback = InteractionFeedback(**feedback_data.dict())
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return feedback

@router.get("/feedback", response_model=List[InteractionFeedbackResponse])
async def get_interaction_feedback(
    question_id: Optional[str] = Query(None),
    responder_id: Optional[str] = Query(None),
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get interaction feedback with filtering"""

    query = db.query(InteractionFeedback)

    if question_id:
        query = query.filter(InteractionFeedback.question_id == question_id)
    if responder_id:
        query = query.filter(InteractionFeedback.responder_id == responder_id)
    if min_rating:
        query = query.filter(InteractionFeedback.interaction_rating >= min_rating)

    feedback = (
        query.order_by(InteractionFeedback.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return feedback

# Communication Patterns
@router.get(
    "/communication-patterns", response_model=List[CommunicationPatternResponse]
)
async def get_communication_patterns(
    profile_id: Optional[str] = Query(None),
    pattern_type: Optional[str] = Query(None),
    min_effectiveness: Optional[float] = Query(None, ge=0.0, le=1.0),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get learned communication patterns"""

    query = db.query(CommunicationPattern).filter(
        CommunicationPattern.is_active == True
    )

    if profile_id:
        query = query.filter(CommunicationPattern.profile_id == profile_id)
    if pattern_type:
        query = query.filter(CommunicationPattern.pattern_type == pattern_type)
    if min_effectiveness:
        query = query.filter(
            CommunicationPattern.effectiveness_score >= min_effectiveness
        )

    patterns = query.order_by(CommunicationPattern.effectiveness_score.desc()).all()
    return patterns

# Analytics and Statistics
@router.get("/analytics/team/{team_id}")
async def get_team_analytics(
    team_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get analytics for team interrogation activities"""

    # Build base query
    question_query = (
        db.query(GeneratedQuestion)
        .join(TeamMemberProfile)
        .filter(TeamMemberProfile.team_id == team_id)
    )

    if start_date:
        question_query = question_query.filter(
            GeneratedQuestion.created_at >= start_date
        )
    if end_date:
        question_query = question_query.filter(GeneratedQuestion.created_at <= end_date)

    # Calculate metrics
    total_questions = question_query.count()

    response_query = (
        db.query(QuestionResponse)
        .join(GeneratedQuestion)
        .join(TeamMemberProfile)
        .filter(TeamMemberProfile.team_id == team_id)
    )

    if start_date:
        response_query = response_query.filter(
            QuestionResponse.created_at >= start_date
        )
    if end_date:
        response_query = response_query.filter(QuestionResponse.created_at <= end_date)

    total_responses = response_query.count()
    completed_responses = response_query.filter(
        QuestionResponse.status == ResponseStatus.COMPLETED
    ).count()

    response_rate = completed_responses / total_questions if total_questions > 0 else 0

    # Average response time
    avg_response_time = (
        db.query(QuestionResponse.response_time_seconds)
        .filter(QuestionResponse.response_time_seconds.isnot(None))
        .join(GeneratedQuestion)
        .join(TeamMemberProfile)
        .filter(TeamMemberProfile.team_id == team_id)
    )

    if start_date:
        avg_response_time = avg_response_time.filter(
            QuestionResponse.created_at >= start_date
        )
    if end_date:
        avg_response_time = avg_response_time.filter(
            QuestionResponse.created_at <= end_date
        )

    response_times = [r[0] for r in avg_response_time.all()]
    avg_time = sum(response_times) / len(response_times) if response_times else 0

    return {
        "team_id": team_id,
        "period": {"start_date": start_date, "end_date": end_date},
        "metrics": {
            "total_questions": total_questions,
            "total_responses": total_responses,
            "completed_responses": completed_responses,
            "response_rate": response_rate,
            "avg_response_time_seconds": avg_time,
        },
    }
