"""
Feedback Loop and Continuous Improvement Service

Handles continuous improvement of the team interrogation system including:
- Interaction quality feedback collection
- Response usefulness tracking for leaders
- Communication preference learning
- Question relevance and timing optimization
- Trust and rapport building measurement
- Intrusion and fatigue prevention
- Continuous model improvement based on feedback
"""

from typing import Any, Dict, List, Optional, Tuple

import statistics
from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.team_interrogation import (CommunicationPattern,
                                         GeneratedQuestion,
                                         InteractionFeedback, QuestionResponse,
                                         QuestionTemplate, QuestionType,
                                         TeamMemberProfile, TrustLevel)
from ..models.user import User
from .communication_service import CommunicationService
from .llm_service import LLMService

class FeedbackImprovementService:
    """Service for feedback collection and continuous improvement"""

    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()
        self.communication_service = CommunicationService(db)

    async def collect_interaction_feedback(
        self, question_id: str, responder_id: str, feedback_data: Dict[str, Any]
    ) -> InteractionFeedback:
        """Collect feedback on an AI interaction"""

        # Validate question and responder exist
        question = (
            self.db.query(GeneratedQuestion)
            .filter(GeneratedQuestion.id == question_id)
            .first()
        )

        if not question:
            raise ValueError("Question not found")

        # Create feedback record
        feedback = InteractionFeedback(
            question_id=question_id, responder_id=responder_id, **feedback_data
        )

        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)

        # Trigger improvement analysis
        await self._analyze_feedback_for_improvements(feedback)

        return feedback

    async def track_response_usefulness(
        self,
        response_id: str,
        leader_user_id: str,
        usefulness_rating: int,
        specific_feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Track how useful responses are for leaders"""

        response = (
            self.db.query(QuestionResponse)
            .filter(QuestionResponse.id == response_id)
            .first()
        )

        if not response:
            return {"error": "Response not found"}

        # Store usefulness tracking
        usefulness_data = {
            "response_id": response_id,
            "leader_user_id": leader_user_id,
            "usefulness_rating": usefulness_rating,
            "specific_feedback": specific_feedback,
            "tracked_at": datetime.utcnow(),
        }

        # Update response quality indicators
        if not response.quality_indicators:
            response.quality_indicators = {}

        response.quality_indicators["leader_usefulness"] = usefulness_rating
        response.quality_indicators["leader_feedback"] = specific_feedback

        self.db.commit()

        # Analyze patterns for improvement
        await self._analyze_usefulness_patterns(response, usefulness_rating)

        return usefulness_data

    async def learn_communication_preferences(
        self, responder_id: str, interaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Learn and update communication preferences"""

        responder = (
            self.db.query(TeamMemberProfile)
            .filter(TeamMemberProfile.id == responder_id)
            .first()
        )

        if not responder:
            return {"error": "Responder not found"}

        # Analyze interaction for preference signals
        preference_updates = await self._extract_preference_signals(interaction_data)

        # Update profile preferences
        updated_fields = []
        for field, new_value in preference_updates.items():
            if hasattr(responder, field):
                old_value = getattr(responder, field)
                setattr(responder, field, new_value)
                updated_fields.append(f"{field}: {old_value} -> {new_value}")

        # Learn communication patterns
        if preference_updates:
            pattern = await self.communication_service.learn_communication_pattern(
                responder_id,
                interaction_data,
                interaction_data.get("effectiveness_score", 0.5),
            )

        responder.updated_at = datetime.utcnow()
        self.db.commit()

        return {
            "responder_id": responder_id,
            "updated_fields": updated_fields,
            "learned_patterns": pattern.id if "pattern" in locals() else None,
            "learning_confidence": await self._calculate_learning_confidence(
                responder_id
            ),
        }

    async def optimize_question_timing(
        self, team_id: Optional[str] = None, member_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Optimize question timing based on response patterns"""

        # Get relevant questions and responses
        query = self.db.query(GeneratedQuestion).join(TeamMemberProfile)

        if team_id:
            query = query.filter(TeamMemberProfile.team_id == team_id)
        if member_id:
            query = query.filter(TeamMemberProfile.id == member_id)

        questions = query.filter(
            GeneratedQuestion.created_at > datetime.utcnow() - timedelta(days=60)
        ).all()

        if not questions:
            return {"error": "Insufficient data for timing optimization"}

        # Analyze timing patterns
        timing_analysis = await self._analyze_timing_effectiveness(questions)

        # Generate timing recommendations
        recommendations = await self._generate_timing_recommendations(timing_analysis)

        # Update profiles with optimized timings
        if member_id:
            await self._update_member_timing_preferences(member_id, recommendations)
        elif team_id:
            await self._update_team_timing_preferences(team_id, recommendations)

        return {
            "scope": f"team_{team_id}" if team_id else f"member_{member_id}",
            "timing_analysis": timing_analysis,
            "recommendations": recommendations,
            "optimization_confidence": timing_analysis.get("confidence_score", 0.0),
        }

    async def measure_trust_building_progress(
        self, member_id: str, timeframe_days: int = 30
    ) -> Dict[str, Any]:
        """Measure trust building progress for a team member"""

        member = (
            self.db.query(TeamMemberProfile)
            .filter(TeamMemberProfile.id == member_id)
            .first()
        )

        if not member:
            return {"error": "Member not found"}

        # Get recent interactions
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=timeframe_days)

        interactions = (
            self.db.query(GeneratedQuestion)
            .filter(
                and_(
                    GeneratedQuestion.recipient_id == member_id,
                    GeneratedQuestion.created_at >= start_date,
                )
            )
            .order_by(GeneratedQuestion.created_at)
            .all()
        )

        if not interactions:
            return {"error": "No recent interactions found"}

        # Analyze trust progression
        trust_metrics = await self._calculate_trust_metrics(member, interactions)

        # Identify trust building factors
        trust_factors = await self._identify_trust_factors(member_id, interactions)

        # Generate trust building recommendations
        trust_recommendations = await self._generate_trust_recommendations(
            member, trust_metrics
        )

        return {
            "member_id": member_id,
            "current_trust_level": member.trust_level,
            "timeframe_days": timeframe_days,
            "trust_metrics": trust_metrics,
            "trust_factors": trust_factors,
            "recommendations": trust_recommendations,
            "projected_improvement": await self._project_trust_improvement(
                member, trust_metrics
            ),
        }

    async def detect_interaction_fatigue(
        self, team_id: Optional[str] = None, member_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Detect signs of interaction fatigue"""

        # Get recent interactions
        query = self.db.query(GeneratedQuestion).join(TeamMemberProfile)

        if team_id:
            query = query.filter(TeamMemberProfile.team_id == team_id)
        if member_id:
            query = query.filter(TeamMemberProfile.id == member_id)

        recent_questions = query.filter(
            GeneratedQuestion.created_at > datetime.utcnow() - timedelta(days=14)
        ).all()

        if not recent_questions:
            return {"fatigue_detected": False, "reason": "No recent interactions"}

        # Analyze fatigue indicators
        fatigue_analysis = await self._analyze_fatigue_indicators(recent_questions)

        # Generate fatigue prevention recommendations
        if fatigue_analysis["fatigue_detected"]:
            prevention_actions = await self._generate_fatigue_prevention_actions(
                fatigue_analysis
            )
        else:
            prevention_actions = []

        return {
            "scope": f"team_{team_id}" if team_id else f"member_{member_id}",
            "fatigue_detected": fatigue_analysis["fatigue_detected"],
            "fatigue_level": fatigue_analysis["fatigue_level"],
            "fatigue_indicators": fatigue_analysis["indicators"],
            "prevention_actions": prevention_actions,
            "recommended_pause_duration": fatigue_analysis.get(
                "recommended_pause", "none"
            ),
        }

    async def improve_question_templates(
        self, category: Optional[str] = None, min_usage_count: int = 5
    ) -> List[Dict[str, Any]]:
        """Improve question templates based on feedback"""

        # Get templates with sufficient usage
        query = self.db.query(QuestionTemplate).filter(
            QuestionTemplate.usage_count >= min_usage_count
        )

        if category:
            query = query.filter(QuestionTemplate.category == category)

        templates = query.all()

        improvements = []

        for template in templates:
            # Analyze template performance
            performance = await self._analyze_template_performance(template)

            # Generate improvements if needed
            if performance["needs_improvement"]:
                improvement_suggestions = await self._generate_template_improvements(
                    template, performance
                )

                improvements.append(
                    {
                        "template_id": template.id,
                        "template_name": template.name,
                        "current_effectiveness": template.effectiveness_score,
                        "performance_analysis": performance,
                        "improvement_suggestions": improvement_suggestions,
                        "priority": self._calculate_improvement_priority(performance),
                    }
                )

        # Sort by improvement priority
        improvements.sort(key=lambda x: x["priority"], reverse=True)

        return improvements

    async def generate_system_improvement_report(
        self, team_id: Optional[str] = None, timeframe_days: int = 30
    ) -> Dict[str, Any]:
        """Generate comprehensive system improvement report"""

        # Collect feedback data
        feedback_query = self.db.query(InteractionFeedback)

        if team_id:
            feedback_query = feedback_query.join(TeamMemberProfile).filter(
                TeamMemberProfile.team_id == team_id
            )

        feedback_data = feedback_query.filter(
            InteractionFeedback.created_at
            > datetime.utcnow() - timedelta(days=timeframe_days)
        ).all()

        if not feedback_data:
            return {"error": "Insufficient feedback data"}

        # Analyze different improvement areas
        report = {
            "report_period": f"{timeframe_days} days",
            "scope": f"team_{team_id}" if team_id else "system_wide",
            "feedback_summary": await self._analyze_feedback_summary(feedback_data),
            "communication_effectiveness": await self._analyze_communication_effectiveness(
                feedback_data
            ),
            "question_quality": await self._analyze_question_quality_trends(
                feedback_data
            ),
            "trust_and_rapport": await self._analyze_trust_trends(feedback_data),
            "fatigue_patterns": await self._analyze_fatigue_patterns(feedback_data),
            "improvement_priorities": [],
            "implementation_roadmap": [],
        }

        # Generate improvement priorities
        priorities = await self._generate_improvement_priorities(report)
        report["improvement_priorities"] = priorities

        # Create implementation roadmap
        roadmap = await self._create_improvement_roadmap(priorities)
        report["implementation_roadmap"] = roadmap

        return report

    # Private helper methods

    async def _analyze_feedback_for_improvements(
        self, feedback: InteractionFeedback
    ) -> None:
        """Analyze feedback to identify improvement opportunities"""

        # Check for low ratings that need attention
        if feedback.interaction_rating <= 2:
            await self._handle_low_rating_feedback(feedback)

        # Learn from positive feedback
        if feedback.interaction_rating >= 4:
            await self._learn_from_positive_feedback(feedback)

        # Update trust metrics
        if feedback.trust_change:
            await self._update_trust_metrics(feedback)

    async def _analyze_usefulness_patterns(
        self, response: QuestionResponse, usefulness_rating: int
    ) -> None:
        """Analyze usefulness patterns to improve question generation"""

        question = response.question

        # If highly useful, reinforce similar question patterns
        if usefulness_rating >= 4:
            if question.template_id:
                template = (
                    self.db.query(QuestionTemplate)
                    .filter(QuestionTemplate.id == question.template_id)
                    .first()
                )
                if template:
                    template.effectiveness_score = min(
                        1.0, template.effectiveness_score + 0.1
                    )

        # If not useful, analyze what went wrong
        elif usefulness_rating <= 2:
            await self._analyze_low_usefulness(question, response)

        self.db.commit()

    async def _extract_preference_signals(
        self, interaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract preference signals from interaction data"""

        preferences = {}

        # Communication style preferences
        if "preferred_formality" in interaction_data:
            preferences["formality_preference"] = interaction_data[
                "preferred_formality"
            ]

        # Channel preferences
        if "preferred_channel" in interaction_data:
            current_channels = interaction_data.get("current_preferred_channels", [])
            new_channel = interaction_data["preferred_channel"]
            if new_channel not in current_channels:
                current_channels.insert(0, new_channel)  # Add to front
                preferences["preferred_channels"] = current_channels[:3]  # Keep top 3

        # Timing preferences
        if "optimal_response_time" in interaction_data:
            preferences["response_time_preference"] = interaction_data[
                "optimal_response_time"
            ]

        return preferences

    async def _calculate_learning_confidence(self, responder_id: str) -> float:
        """Calculate confidence in learned preferences"""

        # Count interactions for confidence calculation
        interaction_count = (
            self.db.query(GeneratedQuestion)
            .filter(GeneratedQuestion.recipient_id == responder_id)
            .count()
        )

        # More interactions = higher confidence
        confidence = min(
            1.0, interaction_count / 20.0
        )  # Max confidence at 20 interactions

        return confidence

    async def _analyze_timing_effectiveness(
        self, questions: List[GeneratedQuestion]
    ) -> Dict[str, Any]:
        """Analyze timing effectiveness patterns"""

        timing_data = []

        for question in questions:
            responses = question.responses
            if responses:
                response = responses[0]  # Take first response

                timing_data.append(
                    {
                        "sent_hour": (
                            question.sent_at.hour if question.sent_at else None
                        ),
                        "sent_day": (
                            question.sent_at.weekday() if question.sent_at else None
                        ),
                        "response_time": response.response_time_seconds,
                        "response_quality": (
                            response.quality_indicators.get("quality_score", 0.5)
                            if response.quality_indicators
                            else 0.5
                        ),
                    }
                )

        # Analyze patterns
        hour_effectiveness = defaultdict(list)
        day_effectiveness = defaultdict(list)

        for data in timing_data:
            if data["sent_hour"] is not None:
                hour_effectiveness[data["sent_hour"]].append(
                    {
                        "response_time": data["response_time"],
                        "quality": data["response_quality"],
                    }
                )

            if data["sent_day"] is not None:
                day_effectiveness[data["sent_day"]].append(
                    {
                        "response_time": data["response_time"],
                        "quality": data["response_quality"],
                    }
                )

        # Calculate effectiveness scores
        best_hours = {}
        for hour, responses in hour_effectiveness.items():
            if len(responses) >= 2:  # Need minimum data
                avg_quality = statistics.mean([r["quality"] for r in responses])
                avg_response_time = statistics.mean(
                    [r["response_time"] for r in responses if r["response_time"]]
                )

                # Combine quality and speed (lower response time is better)
                effectiveness = (
                    avg_quality - (avg_response_time / 3600) * 0.1
                )  # Penalize slow responses
                best_hours[hour] = effectiveness

        best_days = {}
        for day, responses in day_effectiveness.items():
            if len(responses) >= 2:
                avg_quality = statistics.mean([r["quality"] for r in responses])
                best_days[day] = avg_quality

        return {
            "total_questions": len(questions),
            "best_hours": dict(
                sorted(best_hours.items(), key=lambda x: x[1], reverse=True)[:3]
            ),
            "best_days": dict(
                sorted(best_days.items(), key=lambda x: x[1], reverse=True)[:3]
            ),
            "confidence_score": min(1.0, len(timing_data) / 10.0),
        }

    async def _generate_timing_recommendations(
        self, timing_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate timing optimization recommendations"""

        recommendations = []

        if timing_analysis["best_hours"]:
            best_hour = list(timing_analysis["best_hours"].keys())[0]
            recommendations.append(
                f"Optimal sending time: {best_hour}:00-{best_hour+1}:00"
            )

        if timing_analysis["best_days"]:
            best_day = list(timing_analysis["best_days"].keys())[0]
            day_names = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
            recommendations.append(f"Optimal day: {day_names[best_day]}")

        confidence = timing_analysis["confidence_score"]
        if confidence < 0.5:
            recommendations.append(
                "Recommendation: Collect more data for better timing optimization"
            )

        return recommendations

    async def _calculate_trust_metrics(
        self, member: TeamMemberProfile, interactions: List[GeneratedQuestion]
    ) -> Dict[str, Any]:
        """Calculate trust metrics from interactions"""

        if not interactions:
            return {"error": "No interactions to analyze"}

        # Get feedback for these interactions
        interaction_ids = [i.id for i in interactions]
        feedback = (
            self.db.query(InteractionFeedback)
            .filter(InteractionFeedback.question_id.in_(interaction_ids))
            .all()
        )

        trust_metrics = {
            "response_rate": member.response_rate,
            "avg_response_time": member.avg_response_time,
            "interaction_count": len(interactions),
            "feedback_count": len(feedback),
        }

        if feedback:
            trust_metrics.update(
                {
                    "avg_interaction_rating": statistics.mean(
                        [f.interaction_rating for f in feedback]
                    ),
                    "avg_rapport_rating": statistics.mean(
                        [f.rapport_rating for f in feedback if f.rapport_rating]
                    ),
                    "trust_positive_changes": len(
                        [f for f in feedback if f.trust_change == "increased"]
                    ),
                    "trust_negative_changes": len(
                        [f for f in feedback if f.trust_change == "decreased"]
                    ),
                    "avg_intrusion_level": statistics.mean(
                        [f.intrusion_level for f in feedback if f.intrusion_level]
                    ),
                }
            )

        return trust_metrics

    async def _identify_trust_factors(
        self, member_id: str, interactions: List[GeneratedQuestion]
    ) -> Dict[str, Any]:
        """Identify factors affecting trust building"""

        positive_factors = []
        negative_factors = []

        # Analyze response patterns
        response_count = sum(1 for i in interactions if i.responses)
        if response_count / len(interactions) > 0.8:
            positive_factors.append("High response rate")
        elif response_count / len(interactions) < 0.3:
            negative_factors.append("Low response rate")

        # Analyze timing patterns
        avg_response_times = []
        for interaction in interactions:
            if interaction.responses:
                response = interaction.responses[0]
                if response.response_time_seconds:
                    avg_response_times.append(response.response_time_seconds)

        if avg_response_times:
            avg_time_hours = statistics.mean(avg_response_times) / 3600
            if avg_time_hours < 2:
                positive_factors.append("Quick response times")
            elif avg_time_hours > 24:
                negative_factors.append("Slow response times")

        return {
            "positive_factors": positive_factors,
            "negative_factors": negative_factors,
            "trust_trajectory": (
                "improving"
                if len(positive_factors) > len(negative_factors)
                else "declining"
            ),
        }

    async def _analyze_fatigue_indicators(
        self, questions: List[GeneratedQuestion]
    ) -> Dict[str, Any]:
        """Analyze indicators of interaction fatigue"""

        if not questions:
            return {"fatigue_detected": False, "fatigue_level": 0}

        fatigue_indicators = []
        fatigue_score = 0.0

        # Check frequency increase
        questions_by_week = defaultdict(int)
        for question in questions:
            week = question.created_at.strftime("%Y-W%U")
            questions_by_week[week] += 1

        weekly_counts = list(questions_by_week.values())
        if len(weekly_counts) > 1:
            recent_avg = statistics.mean(weekly_counts[-2:])
            early_avg = (
                statistics.mean(weekly_counts[:-2])
                if len(weekly_counts) > 2
                else weekly_counts[0]
            )

            if recent_avg > early_avg * 1.5:
                fatigue_indicators.append("Increasing question frequency")
                fatigue_score += 0.3

        # Check response rate decline
        responses_by_week = defaultdict(list)
        for question in questions:
            week = question.created_at.strftime("%Y-W%U")
            responses_by_week[week].append(1 if question.responses else 0)

        weekly_response_rates = []
        for week, responses in responses_by_week.items():
            weekly_response_rates.append(statistics.mean(responses))

        if len(weekly_response_rates) > 1:
            recent_rate = statistics.mean(weekly_response_rates[-2:])
            early_rate = (
                statistics.mean(weekly_response_rates[:-2])
                if len(weekly_response_rates) > 2
                else weekly_response_rates[0]
            )

            if recent_rate < early_rate * 0.7:
                fatigue_indicators.append("Declining response rate")
                fatigue_score += 0.4

        # Check for feedback about frequency
        feedback = (
            self.db.query(InteractionFeedback)
            .filter(InteractionFeedback.question_id.in_([q.id for q in questions]))
            .all()
        )

        high_intrusion_feedback = [
            f for f in feedback if f.intrusion_level and f.intrusion_level >= 4
        ]
        if len(high_intrusion_feedback) > len(feedback) * 0.3:
            fatigue_indicators.append("High intrusion ratings")
            fatigue_score += 0.3

        fatigue_detected = fatigue_score > 0.5
        fatigue_level = min(1.0, fatigue_score)

        return {
            "fatigue_detected": fatigue_detected,
            "fatigue_level": fatigue_level,
            "indicators": fatigue_indicators,
            "recommended_pause": (
                "1 week"
                if fatigue_level > 0.8
                else "3 days" if fatigue_level > 0.6 else "none"
            ),
        }

    async def _analyze_template_performance(
        self, template: QuestionTemplate
    ) -> Dict[str, Any]:
        """Analyze performance of a question template"""

        # Get questions using this template
        questions = (
            self.db.query(GeneratedQuestion)
            .filter(GeneratedQuestion.template_id == template.id)
            .all()
        )

        if not questions:
            return {"needs_improvement": False, "reason": "No usage data"}

        # Calculate performance metrics
        total_questions = len(questions)
        total_responses = sum(len(q.responses) for q in questions)
        response_rate = total_responses / total_questions if total_questions > 0 else 0

        # Quality metrics
        quality_scores = []
        for question in questions:
            for response in question.responses:
                if response.quality_indicators:
                    quality_scores.append(
                        response.quality_indicators.get("quality_score", 0.5)
                    )

        avg_quality = statistics.mean(quality_scores) if quality_scores else 0.5

        # Feedback metrics
        feedback = (
            self.db.query(InteractionFeedback)
            .filter(InteractionFeedback.question_id.in_([q.id for q in questions]))
            .all()
        )

        avg_rating = (
            statistics.mean([f.interaction_rating for f in feedback])
            if feedback
            else 3.0
        )

        # Determine if improvement is needed
        needs_improvement = (
            response_rate < 0.6
            or avg_quality < 0.6
            or avg_rating < 3.0
            or template.effectiveness_score < 0.5
        )

        return {
            "needs_improvement": needs_improvement,
            "response_rate": response_rate,
            "avg_quality": avg_quality,
            "avg_rating": avg_rating,
            "usage_count": total_questions,
            "feedback_count": len(feedback),
        }

    async def _generate_template_improvements(
        self, template: QuestionTemplate, performance: Dict[str, Any]
    ) -> List[str]:
        """Generate specific improvement suggestions for a template"""

        improvements = []

        if performance["response_rate"] < 0.6:
            improvements.append(
                "Simplify question complexity to increase response rate"
            )

        if performance["avg_quality"] < 0.6:
            improvements.append(
                "Add more context or examples to improve response quality"
            )

        if performance["avg_rating"] < 3.0:
            improvements.append("Adjust tone or approach based on user feedback")

        # Use LLM for specific suggestions
        llm_suggestions = await self._get_llm_template_suggestions(
            template, performance
        )
        improvements.extend(llm_suggestions)

        return improvements

    async def _get_llm_template_suggestions(
        self, template: QuestionTemplate, performance: Dict[str, Any]
    ) -> List[str]:
        """Get LLM-generated improvement suggestions"""

        suggestion_prompt = f"""
        Analyze this question template and suggest improvements:

        Template: {template.template_text}
        Category: {template.category}
        Type: {template.question_type}

        Performance Issues:
        - Response Rate: {performance['response_rate']:.2f}
        - Quality Score: {performance['avg_quality']:.2f}
        - User Rating: {performance['avg_rating']:.2f}

        Suggest 2-3 specific improvements to make this template more effective.
        """

        try:
            suggestions_text = await self.llm_service.generate_text(
                prompt=suggestion_prompt, max_tokens=200
            )

            # Parse suggestions (simple line-based parsing)
            suggestions = [
                s.strip()
                for s in suggestions_text.split("\n")
                if s.strip() and not s.startswith("-")
            ]
            return suggestions[:3]  # Return top 3
        except Exception:
            return [
                "Review template wording for clarity",
                "Consider adding examples or context",
            ]

    def _calculate_improvement_priority(self, performance: Dict[str, Any]) -> float:
        """Calculate priority score for template improvement"""

        priority = 0.0

        # High usage but poor performance = high priority
        if performance["usage_count"] > 10:
            priority += 0.3

        # Poor metrics = higher priority
        if performance["response_rate"] < 0.5:
            priority += 0.4
        if performance["avg_quality"] < 0.5:
            priority += 0.3
        if performance["avg_rating"] < 2.5:
            priority += 0.5

        return min(1.0, priority)

    # Additional analysis methods for comprehensive reporting
    async def _analyze_feedback_summary(
        self, feedback_data: List[InteractionFeedback]
    ) -> Dict[str, Any]:
        """Analyze overall feedback summary"""

        if not feedback_data:
            return {}

        return {
            "total_feedback": len(feedback_data),
            "avg_interaction_rating": statistics.mean(
                [f.interaction_rating for f in feedback_data]
            ),
            "avg_relevance": statistics.mean(
                [f.question_relevance for f in feedback_data if f.question_relevance]
            ),
            "avg_clarity": statistics.mean(
                [f.question_clarity for f in feedback_data if f.question_clarity]
            ),
            "positive_trust_changes": len(
                [f for f in feedback_data if f.trust_change == "increased"]
            ),
            "negative_trust_changes": len(
                [f for f in feedback_data if f.trust_change == "decreased"]
            ),
        }

    async def _generate_improvement_priorities(
        self, report: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate prioritized improvement recommendations"""

        priorities = []

        # Analyze each area and generate priorities
        feedback_summary = report.get("feedback_summary", {})

        if feedback_summary.get("avg_interaction_rating", 3.0) < 3.0:
            priorities.append(
                {
                    "area": "User Experience",
                    "priority": "high",
                    "issue": "Low interaction ratings",
                    "action": "Review and improve question quality and communication style",
                }
            )

        # Add more priority analysis...

        return priorities

    async def _create_improvement_roadmap(
        self, priorities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Create implementation roadmap for improvements"""

        roadmap = []

        for i, priority in enumerate(priorities):
            roadmap.append(
                {
                    "phase": i + 1,
                    "timeline": (
                        "immediate"
                        if priority["priority"] == "high"
                        else "within_month"
                    ),
                    "action": priority["action"],
                    "expected_impact": (
                        "improve user satisfaction"
                        if "User Experience" in priority["area"]
                        else "system efficiency"
                    ),
                }
            )

        return roadmap

    # Placeholder methods for additional functionality
    async def _handle_low_rating_feedback(self, feedback: InteractionFeedback) -> None:
        """Handle low rating feedback"""
        pass

    async def _learn_from_positive_feedback(
        self, feedback: InteractionFeedback
    ) -> None:
        """Learn from positive feedback"""
        pass

    async def _update_trust_metrics(self, feedback: InteractionFeedback) -> None:
        """Update trust metrics based on feedback"""
        pass
