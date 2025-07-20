"""
Adaptive Communication and Tone Management Service

Provides intelligent communication adaptation for team interrogation including:
- Communication style adaptation based on relationship history
- Formality level adjustment per individual preferences
- Cultural sensitivity and localization support
- Tone analysis and optimization based on response quality
- Personality-based communication approach
- Trust-building conversation patterns
"""

from typing import Any, Dict, List, Optional, Tuple

from datetime import datetime, timedelta

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.team_interrogation import (CommunicationPattern,
                                         CommunicationStyle, GeneratedQuestion,
                                         InteractionFeedback, QuestionResponse,
                                         TeamMemberProfile, TrustLevel)
from ..models.user import User
from .llm_service import LLMService
from .memory_service import MemoryService

class CommunicationService:
    """Service for adaptive communication and tone management"""

    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()
        self.memory_service = MemoryService(db)

        # Cultural communication patterns
        self.cultural_patterns = {
            "us": {"directness": 0.8, "formality": 0.4, "context": "low"},
            "uk": {"directness": 0.6, "formality": 0.7, "context": "medium"},
            "jp": {"directness": 0.3, "formality": 0.9, "context": "high"},
            "de": {"directness": 0.9, "formality": 0.6, "context": "low"},
            "in": {"directness": 0.5, "formality": 0.8, "context": "high"},
            "br": {"directness": 0.6, "formality": 0.5, "context": "medium"},
            "cn": {"directness": 0.4, "formality": 0.8, "context": "high"},
            "fr": {"directness": 0.7, "formality": 0.7, "context": "medium"},
        }

    async def adapt_message_for_recipient(
        self,
        message: str,
        recipient_profile: TeamMemberProfile,
        context: Dict[str, Any],
        message_type: str = "question",
    ) -> str:
        """Adapt a message for a specific recipient based on their communication preferences"""

        # Get communication patterns for this recipient
        patterns = await self._get_effective_patterns(recipient_profile)

        # Determine optimal communication style
        style = await self._determine_communication_style(
            recipient_profile, context, patterns
        )

        # Apply cultural sensitivity if needed
        if recipient_profile.cultural_context:
            style = await self._apply_cultural_adaptation(
                style, recipient_profile.cultural_context
            )

        # Generate adapted message
        adapted_message = await self._generate_adapted_message(
            message, recipient_profile, style, context, message_type
        )

        return adapted_message

    async def analyze_communication_effectiveness(
        self,
        question_id: str,
        response: QuestionResponse,
        feedback: Optional[InteractionFeedback] = None,
    ) -> Dict[str, Any]:
        """Analyze the effectiveness of communication for a specific interaction"""

        question = (
            self.db.query(GeneratedQuestion)
            .filter(GeneratedQuestion.id == question_id)
            .first()
        )

        if not question:
            return {}

        recipient = question.recipient

        # Calculate effectiveness metrics
        effectiveness = {
            "response_received": response is not None,
            "response_quality": (
                self._assess_response_quality(response) if response else 0.0
            ),
            "response_time": (
                self._calculate_response_time_score(question, response)
                if response
                else 0.0
            ),
            "sentiment_score": (
                response.sentiment_score
                if response and response.sentiment_score
                else 0.0
            ),
            "trust_impact": await self._assess_trust_impact(recipient, feedback),
            "communication_scores": {},
        }

        if feedback:
            effectiveness["communication_scores"] = {
                "clarity": (
                    feedback.question_clarity / 5.0
                    if feedback.question_clarity
                    else 0.5
                ),
                "relevance": (
                    feedback.question_relevance / 5.0
                    if feedback.question_relevance
                    else 0.5
                ),
                "tone": feedback.tone_rating / 5.0 if feedback.tone_rating else 0.5,
                "timing": (
                    feedback.timing_appropriateness / 5.0
                    if feedback.timing_appropriateness
                    else 0.5
                ),
                "intrusion": (
                    1.0 - (feedback.intrusion_level / 5.0)
                    if feedback.intrusion_level
                    else 0.5
                ),
            }

        # Calculate overall effectiveness score
        effectiveness["overall_score"] = self._calculate_overall_effectiveness(
            effectiveness
        )

        return effectiveness

    async def learn_communication_pattern(
        self,
        profile_id: str,
        interaction_data: Dict[str, Any],
        effectiveness_score: float,
    ) -> CommunicationPattern:
        """Learn and store a new communication pattern based on successful interactions"""

        # Analyze interaction for pattern identification
        pattern_analysis = await self._identify_communication_patterns(interaction_data)

        # Check if similar pattern exists
        existing_pattern = (
            self.db.query(CommunicationPattern)
            .filter(
                and_(
                    CommunicationPattern.profile_id == profile_id,
                    CommunicationPattern.pattern_type == pattern_analysis["type"],
                    CommunicationPattern.is_active == True,
                )
            )
            .first()
        )

        if existing_pattern:
            # Update existing pattern
            existing_pattern.effectiveness_score = (
                existing_pattern.effectiveness_score
                * existing_pattern.learned_from_interactions
                + effectiveness_score
            ) / (existing_pattern.learned_from_interactions + 1)
            existing_pattern.learned_from_interactions += 1
            existing_pattern.last_reinforcement = datetime.utcnow()
            existing_pattern.parameters.update(pattern_analysis["parameters"])

            self.db.commit()
            return existing_pattern

        # Create new pattern
        pattern = CommunicationPattern(
            profile_id=profile_id,
            pattern_name=pattern_analysis["name"],
            pattern_type=pattern_analysis["type"],
            parameters=pattern_analysis["parameters"],
            effectiveness_score=effectiveness_score,
            confidence_level=0.5,  # Start with medium confidence
            learned_from_interactions=1,
            conditions=pattern_analysis.get("conditions", {}),
        )

        self.db.add(pattern)
        self.db.commit()
        self.db.refresh(pattern)

        return pattern

    async def suggest_communication_improvements(
        self, profile_id: str, recent_interactions: int = 10
    ) -> Dict[str, Any]:
        """Suggest communication improvements based on recent interaction patterns"""

        profile = (
            self.db.query(TeamMemberProfile)
            .filter(TeamMemberProfile.id == profile_id)
            .first()
        )

        if not profile:
            return {}

        # Get recent questions and responses
        recent_questions = (
            self.db.query(GeneratedQuestion)
            .filter(GeneratedQuestion.recipient_id == profile_id)
            .order_by(GeneratedQuestion.created_at.desc())
            .limit(recent_interactions)
            .all()
        )

        # Analyze patterns in feedback
        feedback_analysis = await self._analyze_feedback_patterns(profile_id)

        # Generate suggestions
        suggestions = {
            "communication_style": await self._suggest_style_adjustments(
                profile, feedback_analysis
            ),
            "timing_optimization": await self._suggest_timing_improvements(
                profile, recent_questions
            ),
            "tone_adjustments": await self._suggest_tone_improvements(
                profile, feedback_analysis
            ),
            "formality_recommendations": await self._suggest_formality_changes(
                profile, feedback_analysis
            ),
            "trust_building": await self._suggest_trust_building_actions(
                profile, feedback_analysis
            ),
        }

        # Priority ranking
        suggestions["priority_order"] = self._rank_suggestion_priorities(
            suggestions, feedback_analysis
        )

        return suggestions

    async def generate_culturally_sensitive_message(
        self,
        base_message: str,
        cultural_context: Dict[str, Any],
        recipient_profile: TeamMemberProfile,
    ) -> str:
        """Generate a culturally sensitive version of a message"""

        culture_code = cultural_context.get("country_code", "us").lower()
        cultural_pattern = self.cultural_patterns.get(
            culture_code, self.cultural_patterns["us"]
        )

        adaptation_prompt = f"""
        Adapt this message for cultural sensitivity:

        Base Message: {base_message}

        Cultural Context:
        - Country: {cultural_context.get("country", "United States")}
        - Language: {cultural_context.get("language", "English")}
        - Cultural Pattern: {json.dumps(cultural_pattern, indent=2)}

        Recipient Profile:
        - Role: {recipient_profile.role}
        - Preferred Style: {recipient_profile.preferred_style}
        - Formality Preference: {recipient_profile.formality_preference}

        Cultural Adaptation Guidelines:
        - Directness Level: {cultural_pattern["directness"]} (0.0=indirect, 1.0=very direct)
        - Formality Level: {cultural_pattern["formality"]} (0.0=casual, 1.0=very formal)
        - Context Level: {cultural_pattern["context"]} (low/medium/high context communication)

        Adapt the message to be culturally appropriate while maintaining the core intent.
        Return only the adapted message.
        """

        adapted_message = await self.llm_service.generate_text(
            prompt=adaptation_prompt, max_tokens=200
        )

        return adapted_message.strip()

    async def build_trust_through_communication(
        self,
        profile_id: str,
        current_trust_level: TrustLevel,
        interaction_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate trust-building communication strategies"""

        profile = (
            self.db.query(TeamMemberProfile)
            .filter(TeamMemberProfile.id == profile_id)
            .first()
        )

        trust_strategies = {
            TrustLevel.LOW: {
                "approach": "gentle_introduction",
                "tone": "respectful_cautious",
                "frequency": "minimal",
                "transparency": "high",
                "value_demonstration": "immediate",
            },
            TrustLevel.BUILDING: {
                "approach": "consistent_reliability",
                "tone": "professional_friendly",
                "frequency": "regular_spaced",
                "transparency": "high",
                "value_demonstration": "consistent",
            },
            TrustLevel.MODERATE: {
                "approach": "collaborative",
                "tone": "natural_conversational",
                "frequency": "adaptive",
                "transparency": "balanced",
                "value_demonstration": "ongoing",
            },
            TrustLevel.HIGH: {
                "approach": "partnership",
                "tone": "comfortable_direct",
                "frequency": "as_needed",
                "transparency": "selective",
                "value_demonstration": "assumed",
            },
            TrustLevel.EXCELLENT: {
                "approach": "seamless_integration",
                "tone": "natural_intuitive",
                "frequency": "optimal",
                "transparency": "contextual",
                "value_demonstration": "implicit",
            },
        }

        current_strategy = trust_strategies.get(
            current_trust_level, trust_strategies[TrustLevel.BUILDING]
        )

        # Generate specific trust-building actions
        trust_actions = await self._generate_trust_actions(
            profile, current_strategy, interaction_history
        )

        return {
            "current_trust_level": current_trust_level,
            "strategy": current_strategy,
            "specific_actions": trust_actions,
            "success_indicators": await self._define_trust_success_indicators(
                current_trust_level
            ),
            "risk_factors": await self._identify_trust_risk_factors(
                profile, interaction_history
            ),
        }

    # Private helper methods

    async def _get_effective_patterns(
        self, profile: TeamMemberProfile
    ) -> List[CommunicationPattern]:
        """Get effective communication patterns for a profile"""

        return (
            self.db.query(CommunicationPattern)
            .filter(
                and_(
                    CommunicationPattern.profile_id == profile.id,
                    CommunicationPattern.is_active == True,
                    CommunicationPattern.effectiveness_score > 0.6,
                )
            )
            .order_by(CommunicationPattern.effectiveness_score.desc())
            .all()
        )

    async def _determine_communication_style(
        self,
        profile: TeamMemberProfile,
        context: Dict[str, Any],
        patterns: List[CommunicationPattern],
    ) -> Dict[str, Any]:
        """Determine optimal communication style for this interaction"""

        # Base style from profile preferences
        base_style = {
            "formality": profile.formality_preference,
            "directness": (
                0.7 if profile.preferred_style == CommunicationStyle.DIRECT else 0.5
            ),
            "warmth": (
                0.8 if profile.preferred_style == CommunicationStyle.SUPPORTIVE else 0.5
            ),
            "technical_level": 0.8 if "technical" in profile.expertise_areas else 0.4,
        }

        # Adjust based on context
        if context.get("urgency") == "high":
            base_style["directness"] += 0.2
            base_style["formality"] += 0.1

        if context.get("sensitive_topic", False):
            base_style["warmth"] += 0.2
            base_style["directness"] -= 0.1

        # Apply learned patterns
        for pattern in patterns:
            if self._pattern_applies_to_context(pattern, context):
                self._apply_pattern_adjustments(base_style, pattern)

        # Normalize values
        for key in base_style:
            base_style[key] = max(0.0, min(1.0, base_style[key]))

        return base_style

    async def _apply_cultural_adaptation(
        self, style: Dict[str, Any], cultural_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply cultural adaptations to communication style"""

        culture_code = cultural_context.get("country_code", "us").lower()
        cultural_pattern = self.cultural_patterns.get(
            culture_code, self.cultural_patterns["us"]
        )

        # Blend personal preferences with cultural norms
        adapted_style = style.copy()
        adapted_style["formality"] = (style["formality"] * 0.6) + (
            cultural_pattern["formality"] * 0.4
        )
        adapted_style["directness"] = (style["directness"] * 0.7) + (
            cultural_pattern["directness"] * 0.3
        )

        # Add cultural-specific adjustments
        if cultural_pattern["context"] == "high":
            adapted_style["context_richness"] = 0.8
        elif cultural_pattern["context"] == "low":
            adapted_style["context_richness"] = 0.3
        else:
            adapted_style["context_richness"] = 0.5

        return adapted_style

    async def _generate_adapted_message(
        self,
        message: str,
        profile: TeamMemberProfile,
        style: Dict[str, Any],
        context: Dict[str, Any],
        message_type: str,
    ) -> str:
        """Generate an adapted message using the determined style"""

        adaptation_prompt = f"""
        Adapt this {message_type} for the specific recipient and communication style:

        Original Message: {message}

        Recipient Profile:
        - Name: {profile.user.first_name if profile.user else "Team Member"}
        - Role: {profile.role}
        - Seniority: {profile.seniority_level}
        - Trust Level: {profile.trust_level}
        - Response Rate: {profile.response_rate}

        Communication Style Parameters:
        - Formality: {style["formality"]:.2f} (0.0=very casual, 1.0=very formal)
        - Directness: {style["directness"]:.2f} (0.0=indirect, 1.0=very direct)
        - Warmth: {style["warmth"]:.2f} (0.0=neutral, 1.0=very warm)
        - Technical Level: {style["technical_level"]:.2f} (0.0=simple, 1.0=technical)
        - Context Richness: {style.get("context_richness", 0.5):.2f} (0.0=minimal context, 1.0=rich context)

        Context: {json.dumps(context, indent=2)}

        Adaptation Guidelines:
        1. Adjust formality level according to the score
        2. Match directness preference - higher scores = more direct
        3. Include appropriate warmth and personal touch
        4. Match technical complexity to recipient's expertise
        5. Provide context richness appropriate for their communication culture
        6. Maintain the core intent and information
        7. Use language that builds trust and rapport

        Return only the adapted message.
        """

        adapted_message = await self.llm_service.generate_text(
            prompt=adaptation_prompt, max_tokens=250
        )

        return adapted_message.strip()

    def _assess_response_quality(self, response: QuestionResponse) -> float:
        """Assess the quality of a response"""

        if not response:
            return 0.0

        quality_score = 0.0

        # Response completeness
        if response.status == "completed":
            quality_score += 0.4
        elif response.status == "partial":
            quality_score += 0.2

        # Response length and detail (for text responses)
        if response.response_text:
            word_count = len(response.response_text.split())
            if word_count > 20:
                quality_score += 0.3
            elif word_count > 5:
                quality_score += 0.2
            else:
                quality_score += 0.1

        # Sentiment positivity
        if response.sentiment_score:
            if response.sentiment_score > 0:
                quality_score += 0.2
            elif response.sentiment_score > -0.3:
                quality_score += 0.1

        # Confidence level
        if response.confidence and response.confidence > 0.7:
            quality_score += 0.1

        return min(1.0, quality_score)

    def _calculate_response_time_score(
        self, question: GeneratedQuestion, response: QuestionResponse
    ) -> float:
        """Calculate response time effectiveness score"""

        if not response or not response.completed_at:
            return 0.0

        # Get expected response time from profile
        expected_hours = question.recipient.response_time_preference

        # Calculate actual response time
        actual_hours = (
            (response.completed_at - question.sent_at).total_seconds() / 3600
            if question.sent_at
            else 0
        )

        # Score based on how close to expected time
        if actual_hours <= expected_hours:
            return 1.0
        elif actual_hours <= expected_hours * 2:
            return 0.7
        elif actual_hours <= expected_hours * 3:
            return 0.4
        else:
            return 0.1

    async def _assess_trust_impact(
        self, profile: TeamMemberProfile, feedback: Optional[InteractionFeedback]
    ) -> float:
        """Assess the impact on trust from this interaction"""

        if not feedback:
            return 0.0

        trust_impact = 0.0

        # Direct trust feedback
        if feedback.trust_change == "increased":
            trust_impact += 0.4
        elif feedback.trust_change == "unchanged":
            trust_impact += 0.2
        elif feedback.trust_change == "decreased":
            trust_impact -= 0.3

        # Rapport rating impact
        if feedback.rapport_rating:
            trust_impact += (feedback.rapport_rating - 3) * 0.1  # 3 is neutral

        # Intrusion level impact (inverted)
        if feedback.intrusion_level:
            trust_impact -= (feedback.intrusion_level - 3) * 0.1

        return trust_impact

    def _calculate_overall_effectiveness(self, effectiveness: Dict[str, Any]) -> float:
        """Calculate overall communication effectiveness score"""

        weights = {
            "response_received": 0.3,
            "response_quality": 0.25,
            "response_time": 0.15,
            "sentiment_score": 0.1,
            "trust_impact": 0.2,
        }

        score = 0.0
        total_weight = 0.0

        for metric, weight in weights.items():
            if metric in effectiveness and effectiveness[metric] is not None:
                if metric == "sentiment_score":
                    # Convert sentiment to 0-1 scale
                    normalized_sentiment = (effectiveness[metric] + 1) / 2
                    score += normalized_sentiment * weight
                else:
                    score += effectiveness[metric] * weight
                total_weight += weight

        # Include communication scores if available
        if effectiveness.get("communication_scores"):
            comm_scores = effectiveness["communication_scores"]
            avg_comm_score = sum(comm_scores.values()) / len(comm_scores)
            score += avg_comm_score * 0.2
            total_weight += 0.2

        return score / total_weight if total_weight > 0 else 0.0

    async def _identify_communication_patterns(
        self, interaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Identify communication patterns from interaction data"""

        # Analyze message characteristics
        message_analysis = await self._analyze_message_characteristics(
            interaction_data.get("message", "")
        )

        # Determine pattern type based on successful elements
        pattern_type = "tone"  # Default
        if interaction_data.get("timing_success", False):
            pattern_type = "timing"
        elif interaction_data.get("formality_success", False):
            pattern_type = "formality"
        elif interaction_data.get("cultural_success", False):
            pattern_type = "cultural"

        return {
            "name": f"effective_{pattern_type}_{datetime.utcnow().strftime('%Y%m%d')}",
            "type": pattern_type,
            "parameters": {
                "message_characteristics": message_analysis,
                "context": interaction_data.get("context", {}),
                "success_factors": interaction_data.get("success_factors", []),
            },
            "conditions": interaction_data.get("conditions", {}),
        }

    async def _analyze_message_characteristics(self, message: str) -> Dict[str, Any]:
        """Analyze characteristics of a message"""

        analysis_prompt = f"""
        Analyze the communication characteristics of this message:

        Message: {message}

        Provide analysis in this JSON format:
        {{
            "formality_level": 0.0-1.0,
            "directness_level": 0.0-1.0,
            "warmth_level": 0.0-1.0,
            "technical_complexity": 0.0-1.0,
            "sentence_structure": "simple|complex",
            "tone": "formal|casual|friendly|professional|supportive",
            "question_type": "open|closed|multiple_choice|scale",
            "context_richness": 0.0-1.0
        }}

        Return only the JSON, no explanation.
        """

        try:
            analysis_text = await self.llm_service.generate_text(
                prompt=analysis_prompt, max_tokens=200
            )
            return json.loads(analysis_text.strip())
        except Exception:
            # Fallback to basic analysis
            return {
                "formality_level": 0.5,
                "directness_level": 0.5,
                "warmth_level": 0.5,
                "technical_complexity": 0.5,
                "sentence_structure": "simple",
                "tone": "professional",
                "question_type": "open",
                "context_richness": 0.5,
            }

    def _pattern_applies_to_context(
        self, pattern: CommunicationPattern, context: Dict[str, Any]
    ) -> bool:
        """Check if a communication pattern applies to the current context"""

        if not pattern.conditions:
            return True

        # Check context matching
        for condition, value in pattern.conditions.items():
            if condition in context and context[condition] != value:
                return False

        return True

    def _apply_pattern_adjustments(
        self, style: Dict[str, Any], pattern: CommunicationPattern
    ) -> None:
        """Apply pattern adjustments to communication style"""

        parameters = pattern.parameters.get("message_characteristics", {})
        effectiveness = pattern.effectiveness_score

        # Apply adjustments weighted by effectiveness
        adjustment_factor = effectiveness * 0.3  # Max 30% adjustment

        for param, value in parameters.items():
            if param.endswith("_level") and param.replace("_level", "") in style:
                style_key = param.replace("_level", "")
                current_value = style[style_key]
                adjustment = (value - current_value) * adjustment_factor
                style[style_key] += adjustment

    async def _analyze_feedback_patterns(self, profile_id: str) -> Dict[str, Any]:
        """Analyze patterns in interaction feedback"""

        recent_feedback = (
            self.db.query(InteractionFeedback)
            .filter(InteractionFeedback.responder_id == profile_id)
            .order_by(InteractionFeedback.created_at.desc())
            .limit(20)
            .all()
        )

        if not recent_feedback:
            return {}

        # Aggregate feedback metrics
        total_feedback = len(recent_feedback)
        avg_ratings = {
            "interaction": sum(f.interaction_rating for f in recent_feedback)
            / total_feedback,
            "relevance": sum(
                f.question_relevance for f in recent_feedback if f.question_relevance
            )
            / len([f for f in recent_feedback if f.question_relevance]),
            "clarity": sum(
                f.question_clarity for f in recent_feedback if f.question_clarity
            )
            / len([f for f in recent_feedback if f.question_clarity]),
            "tone": sum(f.tone_rating for f in recent_feedback if f.tone_rating)
            / len([f for f in recent_feedback if f.tone_rating]),
            "timing": sum(
                f.timing_appropriateness
                for f in recent_feedback
                if f.timing_appropriateness
            )
            / len([f for f in recent_feedback if f.timing_appropriateness]),
        }

        # Identify trends
        recent_half = recent_feedback[: total_feedback // 2]
        older_half = recent_feedback[total_feedback // 2 :]

        trends = {}
        if recent_half and older_half:
            trends = {
                "interaction_trend": (
                    sum(f.interaction_rating for f in recent_half) / len(recent_half)
                )
                - (sum(f.interaction_rating for f in older_half) / len(older_half)),
                "trust_improvements": len(
                    [f for f in recent_half if f.trust_change == "increased"]
                ),
                "trust_declines": len(
                    [f for f in recent_half if f.trust_change == "decreased"]
                ),
            }

        return {
            "total_feedback": total_feedback,
            "average_ratings": avg_ratings,
            "trends": trends,
            "common_suggestions": [
                f.suggestions for f in recent_feedback if f.suggestions
            ],
        }

    async def _suggest_style_adjustments(
        self, profile: TeamMemberProfile, feedback_analysis: Dict[str, Any]
    ) -> List[str]:
        """Suggest communication style adjustments"""

        suggestions = []
        avg_ratings = feedback_analysis.get("average_ratings", {})

        if avg_ratings.get("tone", 3.0) < 3.5:
            if profile.preferred_style == CommunicationStyle.FORMAL:
                suggestions.append(
                    "Consider adding more warmth while maintaining professionalism"
                )
            else:
                suggestions.append(
                    "Adjust tone to be more aligned with recipient's communication style"
                )

        if avg_ratings.get("clarity", 3.0) < 3.5:
            suggestions.append("Simplify language and provide clearer explanations")

        if avg_ratings.get("relevance", 3.0) < 3.5:
            suggestions.append(
                "Better align questions with recipient's current responsibilities"
            )

        return suggestions

    async def _suggest_timing_improvements(
        self, profile: TeamMemberProfile, recent_questions: List[GeneratedQuestion]
    ) -> List[str]:
        """Suggest timing improvements"""

        suggestions = []

        # Analyze response times vs. scheduled times
        response_delays = []
        for question in recent_questions:
            if question.scheduled_for and question.sent_at:
                delay = (
                    question.sent_at - question.scheduled_for
                ).total_seconds() / 3600
                response_delays.append(delay)

        if response_delays and sum(response_delays) / len(response_delays) > 2:
            suggestions.append(
                "Consider adjusting delivery timing based on recipient's availability patterns"
            )

        # Check workload correlation
        if profile.current_workload > 0.8:
            suggestions.append("Reduce question frequency during high workload periods")

        return suggestions

    async def _suggest_tone_improvements(
        self, profile: TeamMemberProfile, feedback_analysis: Dict[str, Any]
    ) -> List[str]:
        """Suggest tone improvements"""

        suggestions = []
        avg_ratings = feedback_analysis.get("average_ratings", {})

        tone_rating = avg_ratings.get("tone", 3.0)

        if tone_rating < 3.0:
            if profile.trust_level in [TrustLevel.LOW, TrustLevel.BUILDING]:
                suggestions.append(
                    "Use more supportive and encouraging tone to build trust"
                )
            else:
                suggestions.append(
                    "Adjust tone to be more conversational and less formal"
                )
        elif tone_rating > 4.5:
            suggestions.append("Maintain current tone - it's working well")

        return suggestions

    async def _suggest_formality_changes(
        self, profile: TeamMemberProfile, feedback_analysis: Dict[str, Any]
    ) -> List[str]:
        """Suggest formality level changes"""

        suggestions = []

        # Check for formality preference feedback
        common_suggestions = feedback_analysis.get("common_suggestions", [])
        formality_mentions = [s for s in common_suggestions if "formal" in s.lower()]

        if formality_mentions:
            if "too formal" in str(formality_mentions).lower():
                suggestions.append(
                    "Reduce formality level for more natural communication"
                )
            elif "more formal" in str(formality_mentions).lower():
                suggestions.append(
                    "Increase formality level to match professional expectations"
                )

        return suggestions

    async def _suggest_trust_building_actions(
        self, profile: TeamMemberProfile, feedback_analysis: Dict[str, Any]
    ) -> List[str]:
        """Suggest trust building actions"""

        suggestions = []
        trends = feedback_analysis.get("trends", {})

        if trends.get("trust_declines", 0) > trends.get("trust_improvements", 0):
            suggestions.extend(
                [
                    "Increase transparency about why questions are being asked",
                    "Provide clearer value proposition for participation",
                    "Reduce question frequency to avoid fatigue",
                    "Follow up on previous responses to show they were valued",
                ]
            )

        if profile.response_rate < 0.5:
            suggestions.extend(
                [
                    "Demonstrate immediate value from responses",
                    "Simplify question complexity",
                    "Provide more context about how responses help the team",
                ]
            )

        return suggestions

    def _rank_suggestion_priorities(
        self, suggestions: Dict[str, List[str]], feedback_analysis: Dict[str, Any]
    ) -> List[str]:
        """Rank suggestions by priority"""

        priorities = []
        avg_ratings = feedback_analysis.get("average_ratings", {})

        # High priority: Critical ratings below 3.0
        if avg_ratings.get("interaction", 3.0) < 3.0:
            priorities.extend(suggestions.get("communication_style", []))

        if avg_ratings.get("trust_impact", 0.0) < 0:
            priorities.extend(suggestions.get("trust_building", []))

        # Medium priority: Ratings between 3.0-3.5
        if 3.0 <= avg_ratings.get("tone", 3.0) < 3.5:
            priorities.extend(suggestions.get("tone_adjustments", []))

        if 3.0 <= avg_ratings.get("timing", 3.0) < 3.5:
            priorities.extend(suggestions.get("timing_optimization", []))

        # Low priority: Other improvements
        priorities.extend(suggestions.get("formality_recommendations", []))

        return priorities[:10]  # Return top 10 priorities

    async def _generate_trust_actions(
        self,
        profile: TeamMemberProfile,
        strategy: Dict[str, str],
        interaction_history: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate specific trust-building actions"""

        actions = []

        if strategy["approach"] == "gentle_introduction":
            actions.extend(
                [
                    "Start with very simple, low-stakes questions",
                    "Always explain why the question is being asked",
                    "Provide immediate acknowledgment of responses",
                    "Share how responses will be used",
                ]
            )
        elif strategy["approach"] == "consistent_reliability":
            actions.extend(
                [
                    "Maintain predictable communication patterns",
                    "Always follow through on commitments made",
                    "Provide regular feedback on response value",
                    "Gradually increase question complexity",
                ]
            )
        elif strategy["approach"] == "collaborative":
            actions.extend(
                [
                    "Include recipient in question formulation process",
                    "Ask for feedback on communication preferences",
                    "Share aggregated insights from their contributions",
                    "Offer choices in question timing and format",
                ]
            )
        elif strategy["approach"] == "partnership":
            actions.extend(
                [
                    "Co-create question strategies",
                    "Provide advanced insights and recommendations",
                    "Enable self-service question answering",
                    "Focus on strategic rather than tactical questions",
                ]
            )
        elif strategy["approach"] == "seamless_integration":
            actions.extend(
                [
                    "Anticipate information needs proactively",
                    "Integrate with existing workflows",
                    "Provide contextual micro-interactions",
                    "Enable ambient information sharing",
                ]
            )

        return actions

    async def _define_trust_success_indicators(
        self, current_level: TrustLevel
    ) -> List[str]:
        """Define success indicators for trust building"""

        indicators = {
            TrustLevel.LOW: [
                "Response rate increases above 30%",
                "Feedback ratings improve to 3.0+",
                "Reduced time to first response",
                "Positive feedback comments about helpfulness",
            ],
            TrustLevel.BUILDING: [
                "Response rate reaches 50%+",
                "Feedback ratings consistently above 3.5",
                "Proactive engagement in conversations",
                "Requests for additional questions or insights",
            ],
            TrustLevel.MODERATE: [
                "Response rate above 70%",
                "High quality detailed responses",
                "Suggestions for improving questions",
                "Voluntary sharing of additional context",
            ],
            TrustLevel.HIGH: [
                "Response rate above 85%",
                "Active participation in question design",
                "Regular unsolicited feedback and insights",
                "Advocacy for the system to other team members",
            ],
            TrustLevel.EXCELLENT: [
                "Near 100% response rate",
                "Seamless integration into daily workflow",
                "Proactive information sharing",
                "System becomes indispensable to their work",
            ],
        }

        return indicators.get(current_level, indicators[TrustLevel.BUILDING])

    async def _identify_trust_risk_factors(
        self, profile: TeamMemberProfile, interaction_history: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify potential trust risk factors"""

        risks = []

        # Response rate declining
        if profile.response_rate < 0.3:
            risks.append("Low response rate indicates disengagement")

        # Recent negative feedback
        recent_negative = len(
            [h for h in interaction_history[-5:] if h.get("feedback_rating", 3) < 3]
        )
        if recent_negative > 2:
            risks.append("Recent negative feedback pattern")

        # High workload
        if profile.current_workload > 0.8:
            risks.append("High workload may impact participation willingness")

        # Long response times
        if profile.avg_response_time > profile.response_time_preference * 2:
            risks.append("Consistently delayed responses suggest low priority")

        # Trust level stagnation
        if len(interaction_history) > 10 and profile.trust_level == TrustLevel.LOW:
            risks.append("Trust level not improving despite interactions")

        return risks
