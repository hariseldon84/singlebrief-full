"""
Context-Aware Team Querying Service

Provides intelligent team querying based on context including:
- Team structure and relationship mapping
- Expertise and knowledge area identification
- Workload and availability consideration
- Recent interaction history awareness
- Project and deadline context integration
- Skip logic for irrelevant team members
- Escalation and delegation query routing
"""

from typing import Any, Dict, List, Optional, Tuple

from datetime import datetime, timedelta

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.team_interrogation import (GeneratedQuestion, QuestionResponse,
                                         QuestionType, ResponseStatus,
                                         TeamMemberProfile)
from ..models.user import User
from .llm_service import LLMService
from .question_generation import QuestionGenerationService

class ContextAwareQueryingService:
    """Service for context-aware team querying and routing"""

    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()
        self.question_service = QuestionGenerationService(db)

    async def route_query_to_relevant_members(
        self,
        team_id: str,
        query_context: Dict[str, Any],
        max_recipients: int = 5,
        required_expertise: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Route a query to the most relevant team members"""

        # Get all team members
        team_members = (
            self.db.query(TeamMemberProfile)
            .filter(TeamMemberProfile.team_id == team_id)
            .all()
        )

        if not team_members:
            return []

        # Score each member for relevance
        member_scores = []
        for member in team_members:
            relevance_score = await self._calculate_member_relevance(
                member, query_context, required_expertise
            )

            if relevance_score["should_include"]:
                member_scores.append(
                    {
                        "member": member,
                        "relevance_score": relevance_score["score"],
                        "reasoning": relevance_score["reasoning"],
                        "routing_priority": relevance_score["priority"],
                    }
                )

        # Sort by relevance and priority
        member_scores.sort(
            key=lambda x: (x["routing_priority"], x["relevance_score"]), reverse=True
        )

        # Apply escalation and delegation logic
        final_routing = await self._apply_escalation_logic(
            member_scores[:max_recipients], query_context
        )

        return final_routing

    async def check_member_availability(
        self, member_id: str, urgency_level: str = "normal"
    ) -> Dict[str, Any]:
        """Check if a team member is available for questioning"""

        member = (
            self.db.query(TeamMemberProfile)
            .filter(TeamMemberProfile.id == member_id)
            .first()
        )

        if not member:
            return {"available": False, "reason": "Member not found"}

        # Check workload
        if member.current_workload > 0.9 and urgency_level != "critical":
            return {
                "available": False,
                "reason": "High workload",
                "suggested_delay": "4 hours",
                "alternative_members": await self._find_alternative_members(member),
            }

        # Check recent interaction frequency
        recent_questions = (
            self.db.query(GeneratedQuestion)
            .filter(
                and_(
                    GeneratedQuestion.recipient_id == member_id,
                    GeneratedQuestion.created_at
                    > datetime.utcnow() - timedelta(days=1),
                )
            )
            .count()
        )

        daily_limit = self._get_daily_question_limit(member, urgency_level)

        if recent_questions >= daily_limit:
            return {
                "available": False,
                "reason": "Daily question limit reached",
                "suggested_delay": "tomorrow",
                "recent_questions": recent_questions,
            }

        # Check typical availability patterns
        current_hour = datetime.utcnow().hour
        availability_score = member.typical_availability.get(str(current_hour), 0.5)

        if availability_score < 0.3 and urgency_level == "normal":
            return {
                "available": False,
                "reason": "Outside typical availability hours",
                "suggested_time": await self._suggest_optimal_time(member),
                "availability_score": availability_score,
            }

        return {
            "available": True,
            "confidence": availability_score,
            "estimated_response_time": f"{member.response_time_preference} hours",
        }

    async def apply_skip_logic(
        self,
        question_context: Dict[str, Any],
        potential_recipients: List[TeamMemberProfile],
    ) -> List[TeamMemberProfile]:
        """Apply skip logic to filter out irrelevant team members"""

        relevant_members = []

        for member in potential_recipients:
            skip_analysis = await self._analyze_skip_conditions(
                member, question_context
            )

            if not skip_analysis["should_skip"]:
                relevant_members.append(member)

        return relevant_members

    async def determine_escalation_path(
        self,
        original_recipient_id: str,
        escalation_reason: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Determine escalation path for unanswered or problematic questions"""

        original_member = (
            self.db.query(TeamMemberProfile)
            .filter(TeamMemberProfile.id == original_recipient_id)
            .first()
        )

        if not original_member:
            return {"error": "Original recipient not found"}

        escalation_options = []

        # Peer escalation - same level colleagues
        if escalation_reason == "expertise_gap":
            peers = await self._find_peers_with_expertise(original_member, context)
            escalation_options.extend(
                [
                    {
                        "type": "peer_escalation",
                        "member": peer,
                        "reasoning": "Colleague with relevant expertise",
                    }
                    for peer in peers
                ]
            )

        # Hierarchical escalation - manager or senior
        if escalation_reason in ["no_response", "authority_needed"]:
            managers = await self._find_reporting_managers(original_member)
            escalation_options.extend(
                [
                    {
                        "type": "hierarchical_escalation",
                        "member": manager,
                        "reasoning": "Reporting manager for authority/follow-up",
                    }
                    for manager in managers
                ]
            )

        # Expertise escalation - subject matter experts
        if escalation_reason == "complex_question":
            experts = await self._find_subject_matter_experts(original_member, context)
            escalation_options.extend(
                [
                    {
                        "type": "expertise_escalation",
                        "member": expert,
                        "reasoning": "Subject matter expert",
                    }
                    for expert in experts
                ]
            )

        # Rank by escalation appropriateness
        ranked_options = await self._rank_escalation_options(
            escalation_options, context
        )

        return {
            "original_member": original_member.id,
            "escalation_reason": escalation_reason,
            "escalation_options": ranked_options,
            "recommended_escalation": ranked_options[0] if ranked_options else None,
        }

    async def analyze_team_structure(self, team_id: str) -> Dict[str, Any]:
        """Analyze team structure and relationships"""

        team_members = (
            self.db.query(TeamMemberProfile)
            .filter(TeamMemberProfile.team_id == team_id)
            .all()
        )

        if not team_members:
            return {"error": "No team members found"}

        # Analyze role distribution
        role_distribution = {}
        seniority_distribution = {}
        expertise_map = defaultdict(list)

        for member in team_members:
            # Count roles
            role_distribution[member.role] = role_distribution.get(member.role, 0) + 1

            # Count seniority levels
            seniority_distribution[member.seniority_level] = (
                seniority_distribution.get(member.seniority_level, 0) + 1
            )

            # Map expertise areas
            for expertise in member.expertise_areas:
                expertise_map[expertise].append(member)

        # Identify potential relationships
        relationships = await self._identify_team_relationships(team_members)

        # Analyze communication patterns
        communication_analysis = await self._analyze_team_communication_patterns(
            team_id
        )

        return {
            "team_id": team_id,
            "total_members": len(team_members),
            "role_distribution": role_distribution,
            "seniority_distribution": seniority_distribution,
            "expertise_coverage": {k: len(v) for k, v in expertise_map.items()},
            "expertise_gaps": await self._identify_expertise_gaps(expertise_map),
            "relationships": relationships,
            "communication_patterns": communication_analysis,
            "query_routing_recommendations": await self._generate_routing_recommendations(
                team_members, expertise_map
            ),
        }

    # Private helper methods

    async def _calculate_member_relevance(
        self,
        member: TeamMemberProfile,
        query_context: Dict[str, Any],
        required_expertise: Optional[List[str]],
    ) -> Dict[str, Any]:
        """Calculate relevance score for a team member"""

        relevance_score = 0.0
        reasoning = []

        # Expertise matching
        if required_expertise:
            expertise_match = len(set(required_expertise) & set(member.expertise_areas))
            if expertise_match > 0:
                expertise_score = expertise_match / len(required_expertise)
                relevance_score += expertise_score * 0.4
                reasoning.append(
                    f"Expertise match: {expertise_match}/{len(required_expertise)} areas"
                )

        # Role relevance
        if query_context.get("relevant_roles"):
            if member.role in query_context["relevant_roles"]:
                relevance_score += 0.3
                reasoning.append(f"Role match: {member.role}")

        # Project involvement
        if query_context.get("project_context"):
            # In a real implementation, would check project assignments
            relevance_score += 0.2
            reasoning.append("Project involvement")

        # Response history quality
        avg_response_quality = await self._get_member_response_quality(member.id)
        relevance_score += avg_response_quality * 0.1

        # Availability factor
        availability = await self.check_member_availability(
            member.id, query_context.get("urgency", "normal")
        )
        if availability["available"]:
            relevance_score += 0.1
        else:
            relevance_score -= 0.2
            reasoning.append(f"Limited availability: {availability['reason']}")

        # Determine priority
        if relevance_score > 0.8:
            priority = "high"
        elif relevance_score > 0.5:
            priority = "medium"
        else:
            priority = "low"

        # Skip logic
        should_include = relevance_score > 0.3 and (
            not required_expertise or expertise_match > 0
        )

        return {
            "score": relevance_score,
            "reasoning": reasoning,
            "priority": priority,
            "should_include": should_include,
        }

    async def _apply_escalation_logic(
        self, member_scores: List[Dict[str, Any]], query_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply escalation logic to routing decisions"""

        # For high-priority or complex queries, ensure senior members are included
        if (
            query_context.get("urgency") == "high"
            or query_context.get("complexity") == "high"
        ):
            senior_members = [
                score
                for score in member_scores
                if score["member"].seniority_level in ["senior", "lead", "principal"]
            ]

            if not senior_members and member_scores:
                # Add the most senior available member
                all_members = [score["member"] for score in member_scores]
                most_senior = max(
                    all_members,
                    key=lambda m: self._get_seniority_rank(m.seniority_level),
                )
                member_scores[0]["routing_priority"] = "escalated"
                member_scores[0]["reasoning"].append(
                    "Escalated due to high priority/complexity"
                )

        return member_scores

    def _get_seniority_rank(self, seniority_level: str) -> int:
        """Get numeric rank for seniority level"""
        ranks = {
            "intern": 1,
            "junior": 2,
            "mid": 3,
            "intermediate": 3,
            "senior": 4,
            "lead": 5,
            "principal": 6,
            "staff": 7,
            "director": 8,
        }
        return ranks.get(seniority_level.lower(), 3)

    async def _find_alternative_members(
        self, unavailable_member: TeamMemberProfile
    ) -> List[str]:
        """Find alternative members with similar expertise"""

        # Find members with overlapping expertise
        alternatives = (
            self.db.query(TeamMemberProfile)
            .filter(
                and_(
                    TeamMemberProfile.team_id == unavailable_member.team_id,
                    TeamMemberProfile.id != unavailable_member.id,
                    TeamMemberProfile.current_workload < 0.8,
                )
            )
            .all()
        )

        # Score by expertise overlap
        scored_alternatives = []
        for alt in alternatives:
            overlap = len(
                set(unavailable_member.expertise_areas) & set(alt.expertise_areas)
            )
            if overlap > 0:
                scored_alternatives.append((alt.id, overlap))

        # Return top alternatives
        scored_alternatives.sort(key=lambda x: x[1], reverse=True)
        return [alt_id for alt_id, _ in scored_alternatives[:3]]

    def _get_daily_question_limit(
        self, member: TeamMemberProfile, urgency_level: str
    ) -> int:
        """Get daily question limit based on member profile and urgency"""

        base_limits = {"junior": 2, "mid": 3, "senior": 5, "lead": 7, "principal": 10}

        base_limit = base_limits.get(member.seniority_level, 3)

        # Adjust for trust level
        trust_multiplier = {
            "low": 0.5,
            "building": 0.7,
            "moderate": 1.0,
            "high": 1.3,
            "excellent": 1.5,
        }.get(member.trust_level, 1.0)

        # Adjust for urgency
        urgency_multiplier = {
            "low": 0.7,
            "normal": 1.0,
            "high": 1.5,
            "critical": 2.0,
        }.get(urgency_level, 1.0)

        return int(base_limit * trust_multiplier * urgency_multiplier)

    async def _suggest_optimal_time(self, member: TeamMemberProfile) -> str:
        """Suggest optimal time to contact member"""

        # Find the hour with highest availability
        max_availability = 0
        best_hour = 9  # Default to 9 AM

        for hour_str, availability in member.typical_availability.items():
            try:
                hour = int(hour_str)
                if availability > max_availability:
                    max_availability = availability
                    best_hour = hour
            except Exception:
                continue

        # Format as readable time
        return f"{best_hour:02d}:00"

    async def _analyze_skip_conditions(
        self, member: TeamMemberProfile, question_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze whether to skip questioning this member"""

        skip_reasons = []

        # Expertise relevance
        required_expertise = question_context.get("required_expertise", [])
        if required_expertise:
            expertise_overlap = set(required_expertise) & set(member.expertise_areas)
            if not expertise_overlap:
                skip_reasons.append("No relevant expertise")

        # Project relevance
        if question_context.get("project_specific"):
            # In real implementation, would check project assignments
            # For now, assume all members could be relevant
            pass

        # Recent similar questions
        recent_similar = await self._check_recent_similar_questions(
            member.id, question_context
        )
        if recent_similar:
            skip_reasons.append("Recently answered similar question")

        # Role exclusions
        if question_context.get("exclude_roles"):
            if member.role in question_context["exclude_roles"]:
                skip_reasons.append(f"Role excluded: {member.role}")

        should_skip = len(skip_reasons) > 0

        return {"should_skip": should_skip, "skip_reasons": skip_reasons}

    async def _check_recent_similar_questions(
        self, member_id: str, question_context: Dict[str, Any]
    ) -> bool:
        """Check if member recently answered similar questions"""

        # Get recent questions for this member
        recent_questions = (
            self.db.query(GeneratedQuestion)
            .filter(
                and_(
                    GeneratedQuestion.recipient_id == member_id,
                    GeneratedQuestion.created_at
                    > datetime.utcnow() - timedelta(days=7),
                )
            )
            .all()
        )

        # Check for similar topics/contexts
        for question in recent_questions:
            if question.context:
                context_overlap = set(question_context.keys()) & set(
                    question.context.keys()
                )
                if len(context_overlap) > 2:  # Significant overlap
                    return True

        return False

    async def _get_member_response_quality(self, member_id: str) -> float:
        """Get average response quality for a member"""

        responses = (
            self.db.query(QuestionResponse)
            .filter(
                and_(
                    QuestionResponse.responder_id == member_id,
                    QuestionResponse.status == ResponseStatus.COMPLETED,
                )
            )
            .limit(10)
            .all()
        )

        if not responses:
            return 0.5  # Default neutral quality

        quality_scores = []
        for response in responses:
            if response.quality_indicators:
                quality_scores.append(
                    response.quality_indicators.get("quality_score", 0.5)
                )

        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.5

    async def _find_peers_with_expertise(
        self, member: TeamMemberProfile, context: Dict[str, Any]
    ) -> List[TeamMemberProfile]:
        """Find peer-level colleagues with relevant expertise"""

        required_expertise = context.get("required_expertise", [])

        peers = (
            self.db.query(TeamMemberProfile)
            .filter(
                and_(
                    TeamMemberProfile.team_id == member.team_id,
                    TeamMemberProfile.id != member.id,
                    TeamMemberProfile.seniority_level == member.seniority_level,
                )
            )
            .all()
        )

        relevant_peers = []
        for peer in peers:
            expertise_overlap = set(required_expertise) & set(peer.expertise_areas)
            if expertise_overlap:
                relevant_peers.append(peer)

        return relevant_peers

    async def _find_reporting_managers(
        self, member: TeamMemberProfile
    ) -> List[TeamMemberProfile]:
        """Find reporting managers for escalation"""

        # In a real implementation, would have organizational hierarchy
        # For now, find senior members in same team
        managers = (
            self.db.query(TeamMemberProfile)
            .filter(
                and_(
                    TeamMemberProfile.team_id == member.team_id,
                    TeamMemberProfile.id != member.id,
                    TeamMemberProfile.seniority_level.in_(
                        ["lead", "principal", "director"]
                    ),
                )
            )
            .all()
        )

        return managers

    async def _find_subject_matter_experts(
        self, member: TeamMemberProfile, context: Dict[str, Any]
    ) -> List[TeamMemberProfile]:
        """Find subject matter experts for complex questions"""

        required_expertise = context.get("required_expertise", [])

        experts = (
            self.db.query(TeamMemberProfile)
            .filter(
                and_(
                    TeamMemberProfile.team_id == member.team_id,
                    TeamMemberProfile.id != member.id,
                )
            )
            .all()
        )

        scored_experts = []
        for expert in experts:
            expertise_score = len(set(required_expertise) & set(expert.expertise_areas))
            if expertise_score > 0:
                # Boost score for senior experts
                if expert.seniority_level in ["senior", "lead", "principal"]:
                    expertise_score *= 1.5
                scored_experts.append((expert, expertise_score))

        # Return top experts
        scored_experts.sort(key=lambda x: x[1], reverse=True)
        return [expert for expert, _ in scored_experts[:3]]

    async def _rank_escalation_options(
        self, escalation_options: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Rank escalation options by appropriateness"""

        # Score each option
        for option in escalation_options:
            score = 0.0
            member = option["member"]

            # Type scoring
            type_scores = {
                "peer_escalation": 0.6,
                "hierarchical_escalation": 0.8,
                "expertise_escalation": 0.9,
            }
            score += type_scores.get(option["type"], 0.5)

            # Member availability
            availability = await self.check_member_availability(
                member.id, context.get("urgency", "normal")
            )
            if availability["available"]:
                score += 0.2

            # Response history
            response_quality = await self._get_member_response_quality(member.id)
            score += response_quality * 0.2

            option["escalation_score"] = score

        # Sort by score
        escalation_options.sort(key=lambda x: x["escalation_score"], reverse=True)

        return escalation_options

    async def _identify_team_relationships(
        self, team_members: List[TeamMemberProfile]
    ) -> Dict[str, Any]:
        """Identify relationships within the team"""

        relationships = {
            "reporting_chains": [],
            "expertise_clusters": [],
            "collaboration_patterns": [],
        }

        # Group by seniority for reporting chains
        by_seniority = {}
        for member in team_members:
            level = member.seniority_level
            if level not in by_seniority:
                by_seniority[level] = []
            by_seniority[level].append(member)

        relationships["reporting_chains"] = by_seniority

        # Group by expertise
        expertise_groups = {}
        for member in team_members:
            for expertise in member.expertise_areas:
                if expertise not in expertise_groups:
                    expertise_groups[expertise] = []
                expertise_groups[expertise].append(member.id)

        relationships["expertise_clusters"] = expertise_groups

        return relationships

    async def _analyze_team_communication_patterns(
        self, team_id: str
    ) -> Dict[str, Any]:
        """Analyze communication patterns within the team"""

        # Get recent interactions
        recent_questions = (
            self.db.query(GeneratedQuestion)
            .join(TeamMemberProfile)
            .filter(
                and_(
                    TeamMemberProfile.team_id == team_id,
                    GeneratedQuestion.created_at
                    > datetime.utcnow() - timedelta(days=30),
                )
            )
            .all()
        )

        patterns = {
            "total_interactions": len(recent_questions),
            "avg_response_rate": 0.0,
            "communication_frequency": {},
            "preferred_channels": {},
        }

        if recent_questions:
            # Calculate response rate
            total_responses = (
                self.db.query(QuestionResponse)
                .filter(
                    QuestionResponse.question_id.in_([q.id for q in recent_questions])
                )
                .count()
            )

            patterns["avg_response_rate"] = total_responses / len(recent_questions)

            # Channel preferences
            channel_counts = {}
            for question in recent_questions:
                channel = question.delivery_channel
                channel_counts[channel] = channel_counts.get(channel, 0) + 1

            patterns["preferred_channels"] = channel_counts

        return patterns

    async def _identify_expertise_gaps(
        self, expertise_map: Dict[str, List]
    ) -> List[str]:
        """Identify expertise areas with insufficient coverage"""

        gaps = []

        for expertise, members in expertise_map.items():
            if len(members) == 1:
                gaps.append(f"{expertise} (single point of failure)")
            elif len(members) == 0:
                gaps.append(f"{expertise} (no coverage)")

        return gaps

    async def _generate_routing_recommendations(
        self, team_members: List[TeamMemberProfile], expertise_map: Dict[str, List]
    ) -> List[str]:
        """Generate recommendations for query routing optimization"""

        recommendations = []

        # Check for expertise gaps
        gaps = await self._identify_expertise_gaps(expertise_map)
        if gaps:
            recommendations.append(f"Address expertise gaps: {', '.join(gaps)}")

        # Check for overloaded members
        overloaded = [m for m in team_members if m.current_workload > 0.8]
        if overloaded:
            recommendations.append(
                f"Consider load balancing for {len(overloaded)} overloaded members"
            )

        # Check for underutilized members
        underutilized = [m for m in team_members if m.response_rate < 0.3]
        if underutilized:
            recommendations.append(
                f"Improve engagement for {len(underutilized)} underutilized members"
            )

        return recommendations
