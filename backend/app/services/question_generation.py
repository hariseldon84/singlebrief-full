"""
Intelligent Question Generation Service

Generates contextually appropriate questions for team members based on:
- Role and expertise
- Current context and projects
- Communication preferences
- Question effectiveness history
"""

from typing import Any, Dict, List, Optional, Tuple

from datetime import datetime, timedelta

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.team_interrogation import (CommunicationStyle, GeneratedQuestion,
                                         QuestionComplexity, QuestionResponse,
                                         QuestionTemplate, QuestionType,
                                         TeamMemberProfile)
from ..models.user import User
from .llm_service import LLMService
from .memory_service import MemoryService

class QuestionGenerationService:
    """Service for intelligent question generation and management"""

    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()
        self.memory_service = MemoryService(db)

    async def generate_question_for_member(
        self,
        recipient_id: str,
        context: Dict[str, Any],
        target_complexity: Optional[QuestionComplexity] = None,
        question_type: Optional[QuestionType] = None,
    ) -> GeneratedQuestion:
        """Generate a contextually appropriate question for a team member"""

        # Get team member profile
        profile = (
            self.db.query(TeamMemberProfile)
            .filter(TeamMemberProfile.id == recipient_id)
            .first()
        )

        if not profile:
            raise ValueError(f"Team member profile not found: {recipient_id}")

        # Determine question parameters
        complexity = target_complexity or self._determine_complexity(profile, context)
        q_type = question_type or self._determine_question_type(profile, context)

        # Find suitable template or generate custom question
        template = await self._find_best_template(profile, complexity, q_type, context)

        if template:
            question_text = await self._customize_template(template, profile, context)
        else:
            question_text = await self._generate_custom_question(
                profile, complexity, q_type, context
            )

        # Create question record
        question = GeneratedQuestion(
            template_id=template.id if template else None,
            recipient_id=recipient_id,
            question_text=question_text,
            question_type=q_type,
            complexity=complexity,
            context=context,
            reasoning=await self._generate_reasoning(profile, context, question_text),
            priority=self._calculate_priority(profile, context),
            delivery_channel=self._select_delivery_channel(profile),
            scheduled_for=self._calculate_delivery_time(profile),
            expires_at=self._calculate_expiry_time(profile),
            quality_score=await self._predict_quality_score(
                profile, question_text, context
            ),
        )

        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)

        # Update template usage if used
        if template:
            template.usage_count += 1
            self.db.commit()

        return question

    async def generate_follow_up_question(
        self, parent_question_id: str, response: QuestionResponse
    ) -> Optional[GeneratedQuestion]:
        """Generate follow-up question based on previous response"""

        parent_question = (
            self.db.query(GeneratedQuestion)
            .filter(GeneratedQuestion.id == parent_question_id)
            .first()
        )

        if not parent_question:
            return None

        # Analyze response for follow-up opportunities
        follow_up_needed = await self._analyze_follow_up_need(parent_question, response)

        if not follow_up_needed:
            return None

        # Generate follow-up context
        follow_up_context = {
            "parent_question": parent_question.question_text,
            "parent_response": response.response_text,
            "response_sentiment": response.sentiment_score,
            "clarification_needed": response.quality_indicators.get(
                "needs_clarification", False
            ),
        }

        # Generate follow-up question
        follow_up = await self.generate_question_for_member(
            recipient_id=response.responder_id,
            context=follow_up_context,
            target_complexity=QuestionComplexity.SIMPLE,  # Follow-ups are usually simpler
            question_type=QuestionType.FOLLOW_UP,
        )

        follow_up.parent_question_id = parent_question_id
        follow_up.follow_up_trigger = "response_analysis"

        self.db.commit()

        return follow_up

    async def generate_batch_questions(
        self, team_id: str, context: Dict[str, Any], max_questions: int = 10
    ) -> List[GeneratedQuestion]:
        """Generate questions for multiple team members"""

        # Get team member profiles
        profiles = (
            self.db.query(TeamMemberProfile)
            .filter(TeamMemberProfile.team_id == team_id)
            .all()
        )

        questions = []

        for profile in profiles[:max_questions]:
            # Check if member should receive question
            if await self._should_question_member(profile, context):
                try:
                    question = await self.generate_question_for_member(
                        recipient_id=profile.id, context=context
                    )
                    questions.append(question)
                except Exception as e:
                    # Log error but continue with other members
                    print(f"Error generating question for {profile.id}: {e}")

        return questions

    async def create_question_template(
        self,
        name: str,
        description: str,
        category: str,
        question_type: QuestionType,
        complexity: QuestionComplexity,
        template_text: str,
        variables: Dict[str, Any],
        target_roles: List[str],
        options: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> QuestionTemplate:
        """Create a new question template"""

        template = QuestionTemplate(
            name=name,
            description=description,
            category=category,
            question_type=question_type,
            complexity=complexity,
            template_text=template_text,
            variables=variables,
            target_roles=target_roles,
            options=options or {},
            tags=tags or [],
        )

        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)

        return template

    async def optimize_question_effectiveness(self, template_id: str) -> None:
        """Optimize question template based on response effectiveness"""

        template = (
            self.db.query(QuestionTemplate)
            .filter(QuestionTemplate.id == template_id)
            .first()
        )

        if not template:
            return

        # Get questions using this template
        questions = (
            self.db.query(GeneratedQuestion)
            .filter(GeneratedQuestion.template_id == template_id)
            .all()
        )

        if not questions:
            return

        # Calculate effectiveness metrics
        total_responses = 0
        quality_sum = 0.0
        response_rate = 0.0

        for question in questions:
            responses = question.responses
            if responses:
                total_responses += len(responses)
                quality_sum += sum(
                    r.quality_indicators.get("quality_score", 0.0) for r in responses
                )
                response_rate += len(
                    [r for r in responses if r.status == "completed"]
                ) / len(responses)

        if total_responses > 0:
            avg_quality = quality_sum / total_responses
            avg_response_rate = response_rate / len(questions)

            # Update template effectiveness
            template.effectiveness_score = (avg_quality * 0.6) + (
                avg_response_rate * 0.4
            )
            self.db.commit()

    # Private helper methods

    def _determine_complexity(
        self, profile: TeamMemberProfile, context: Dict[str, Any]
    ) -> QuestionComplexity:
        """Determine appropriate complexity level for the team member"""

        # Base complexity on role and seniority
        if profile.seniority_level in ["senior", "lead", "principal"]:
            base_complexity = QuestionComplexity.COMPLEX
        elif profile.seniority_level in ["mid", "intermediate"]:
            base_complexity = QuestionComplexity.MODERATE
        else:
            base_complexity = QuestionComplexity.SIMPLE

        # Adjust based on context
        if context.get("technical_topic", False):
            if "technical" in profile.expertise_areas:
                return QuestionComplexity.TECHNICAL

        # Consider trust level
        if profile.trust_level in ["low", "building"]:
            return QuestionComplexity.SIMPLE

        return base_complexity

    def _determine_question_type(
        self, profile: TeamMemberProfile, context: Dict[str, Any]
    ) -> QuestionType:
        """Determine appropriate question type"""

        # Consider communication preferences
        if profile.preferred_style == CommunicationStyle.DIRECT:
            return QuestionType.YES_NO

        # For complex topics, use open-ended
        if context.get("requires_explanation", False):
            return QuestionType.OPEN_ENDED

        # For feedback, use scales
        if context.get("feedback_request", False):
            return QuestionType.SCALE

        # Default to open-ended for more information
        return QuestionType.OPEN_ENDED

    async def _find_best_template(
        self,
        profile: TeamMemberProfile,
        complexity: QuestionComplexity,
        question_type: QuestionType,
        context: Dict[str, Any],
    ) -> Optional[QuestionTemplate]:
        """Find the best matching template for the context"""

        # Query templates matching basic criteria
        query = self.db.query(QuestionTemplate).filter(
            and_(
                QuestionTemplate.question_type == question_type,
                QuestionTemplate.complexity == complexity,
                QuestionTemplate.is_active == True,
            )
        )

        # Filter by role if specified
        if profile.role:
            query = query.filter(QuestionTemplate.target_roles.contains([profile.role]))

        # Order by effectiveness score
        templates = (
            query.order_by(desc(QuestionTemplate.effectiveness_score)).limit(5).all()
        )

        if not templates:
            return None

        # Use the most effective template
        return templates[0]

    async def _customize_template(
        self,
        template: QuestionTemplate,
        profile: TeamMemberProfile,
        context: Dict[str, Any],
    ) -> str:
        """Customize template with specific context and profile information"""

        # Prepare template variables
        variables = {
            "name": profile.user.first_name if profile.user else "Team Member",
            "role": profile.role,
            "team": context.get("team_name", "the team"),
            **context,
            **template.variables,
        }

        # Use LLM to customize the template
        customization_prompt = f"""
        Customize this question template for a team member:

        Template: {template.template_text}

        Team Member Info:
        - Role: {profile.role}
        - Seniority: {profile.seniority_level}
        - Preferred Style: {profile.preferred_style}
        - Expertise: {', '.join(profile.expertise_areas)}

        Context: {json.dumps(context, indent=2)}

        Variables: {json.dumps(variables, indent=2)}

        Generate a natural, personalized question that maintains the template's intent but feels customized for this specific person and context.
        """

        customized_text = await self.llm_service.generate_text(
            prompt=customization_prompt, max_tokens=200
        )

        return customized_text.strip()

    async def _generate_custom_question(
        self,
        profile: TeamMemberProfile,
        complexity: QuestionComplexity,
        question_type: QuestionType,
        context: Dict[str, Any],
    ) -> str:
        """Generate a completely custom question"""

        generation_prompt = f"""
        Generate a {complexity.value} {question_type.value} question for a team member with the following profile:

        Team Member:
        - Role: {profile.role}
        - Seniority: {profile.seniority_level}
        - Communication Style: {profile.preferred_style}
        - Expertise Areas: {', '.join(profile.expertise_areas)}
        - Trust Level: {profile.trust_level}

        Context: {json.dumps(context, indent=2)}

        The question should:
        1. Be appropriate for their role and expertise level
        2. Match their communication style preference
        3. Be relevant to the current context
        4. Encourage honest and detailed responses
        5. Build trust and rapport

        Generate only the question text, nothing else.
        """

        question_text = await self.llm_service.generate_text(
            prompt=generation_prompt, max_tokens=150
        )

        return question_text.strip()

    async def _generate_reasoning(
        self, profile: TeamMemberProfile, context: Dict[str, Any], question_text: str
    ) -> str:
        """Generate reasoning for why this question was asked"""

        reasoning_prompt = f"""
        Explain why this question was generated for this team member:

        Question: {question_text}

        Team Member:
        - Role: {profile.role}
        - Expertise: {', '.join(profile.expertise_areas)}

        Context: {json.dumps(context, indent=2)}

        Provide a brief explanation of the reasoning (1-2 sentences).
        """

        reasoning = await self.llm_service.generate_text(
            prompt=reasoning_prompt, max_tokens=100
        )

        return reasoning.strip()

    def _calculate_priority(
        self, profile: TeamMemberProfile, context: Dict[str, Any]
    ) -> float:
        """Calculate question priority score"""

        priority = 0.5  # Base priority

        # Increase priority for senior roles
        if profile.seniority_level in ["senior", "lead", "principal"]:
            priority += 0.2

        # Increase for high-trust members
        if profile.trust_level in ["high", "excellent"]:
            priority += 0.1

        # Increase for urgent context
        if context.get("urgency", "normal") == "high":
            priority += 0.3

        # Decrease for recent interactions
        if profile.total_questions_received > 5:  # Recent activity
            priority -= 0.1

        return min(1.0, max(0.0, priority))

    def _select_delivery_channel(self, profile: TeamMemberProfile) -> str:
        """Select the best delivery channel for the team member"""

        if profile.preferred_channels:
            return profile.preferred_channels[0]

        # Default based on role
        if profile.role in ["developer", "engineer"]:
            return "slack"
        elif profile.role in ["manager", "director"]:
            return "email"
        else:
            return "slack"

    def _calculate_delivery_time(self, profile: TeamMemberProfile) -> datetime:
        """Calculate optimal delivery time"""

        # Default to immediate delivery
        base_time = datetime.utcnow()

        # Consider workload
        if profile.current_workload > 0.8:
            # Delay for high workload
            return base_time + timedelta(hours=4)

        # Consider typical availability
        current_hour = datetime.utcnow().hour
        availability = profile.typical_availability.get(str(current_hour), 0.5)

        if availability < 0.3:
            # Find next available hour
            for hour_offset in range(1, 12):
                check_hour = (current_hour + hour_offset) % 24
                if profile.typical_availability.get(str(check_hour), 0.5) > 0.5:
                    return base_time + timedelta(hours=hour_offset)

        return base_time

    def _calculate_expiry_time(self, profile: TeamMemberProfile) -> datetime:
        """Calculate question expiry time"""

        base_time = datetime.utcnow()

        # Base expiry on response time preference
        hours = profile.response_time_preference

        # Extend for complex questions
        return base_time + timedelta(hours=hours)

    async def _predict_quality_score(
        self, profile: TeamMemberProfile, question_text: str, context: Dict[str, Any]
    ) -> float:
        """Predict the quality score for this question"""

        # Simple heuristic-based prediction
        score = 0.5

        # Increase for experienced members
        if profile.response_rate > 0.8:
            score += 0.2

        # Increase for high trust
        if profile.trust_level in ["high", "excellent"]:
            score += 0.1

        # Increase for relevant expertise
        relevant_expertise = any(
            area in question_text.lower() for area in profile.expertise_areas
        )
        if relevant_expertise:
            score += 0.2

        return min(1.0, score)

    async def _analyze_follow_up_need(
        self, question: GeneratedQuestion, response: QuestionResponse
    ) -> bool:
        """Analyze if a follow-up question is needed"""

        # Check response indicators
        if response.quality_indicators.get("needs_clarification", False):
            return True

        # Check for incomplete responses
        if response.status == "partial":
            return True

        # Check for conflicting information
        if response.sentiment_score and response.sentiment_score < -0.5:
            return True

        # Check response length for open-ended questions
        if (
            question.question_type == QuestionType.OPEN_ENDED
            and response.response_text
            and len(response.response_text.split()) < 10
        ):
            return True

        return False

    async def _should_question_member(
        self, profile: TeamMemberProfile, context: Dict[str, Any]
    ) -> bool:
        """Determine if a team member should receive a question"""

        # Check recent interaction frequency
        recent_questions = (
            self.db.query(GeneratedQuestion)
            .filter(
                and_(
                    GeneratedQuestion.recipient_id == profile.id,
                    GeneratedQuestion.created_at
                    > datetime.utcnow() - timedelta(days=7),
                )
            )
            .count()
        )

        # Limit frequency based on trust level
        max_weekly_questions = {
            "low": 1,
            "building": 2,
            "moderate": 3,
            "high": 5,
            "excellent": 7,
        }.get(profile.trust_level, 2)

        if recent_questions >= max_weekly_questions:
            return False

        # Check workload
        if profile.current_workload > 0.9:
            return False

        # Check relevance
        if (
            context.get("required_expertise")
            and context["required_expertise"] not in profile.expertise_areas
        ):
            return False

        return True
