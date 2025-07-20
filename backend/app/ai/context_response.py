"""Context-Aware Response Generation Service for SingleBrief.

This module implements intelligent response generation that considers user history,
preferences, and context to provide personalized and relevant AI responses.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import json
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.models.memory import (
    UserMemory, TeamMemory, Conversation, ConversationMessage, Decision,
    UserPreference, UserBehaviorPattern
)
from app.models.user import User
from app.core.database import get_async_session
from app.ai.preference_learning import preference_learning_service
from app.ai.memory_service import memory_service

logger = logging.getLogger(__name__)


class ContextAwareResponseService:
    """Service for generating context-aware, personalized AI responses."""
    
    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
        self.context_window_days = 30  # Days to look back for context
        self.max_context_memories = 20  # Maximum memories to include in context
        self.relevance_threshold = 0.3  # Minimum relevance score for context inclusion
        
    async def generate_contextualized_response(
        self,
        user_id: str,
        query: str,
        conversation_id: Optional[str] = None,
        response_format: Optional[str] = None,
        include_team_context: bool = True
    ) -> Dict[str, Any]:
        """Generate a context-aware response for a user query.
        
        Args:
            user_id: ID of the user making the query
            query: The user's query
            conversation_id: Optional conversation context
            response_format: Preferred response format
            include_team_context: Whether to include team memory context
            
        Returns:
            Dict containing contextualized response components
        """
        session = self.session or await get_async_session().__anext__()
        
        try:
            # Get user preferences for response personalization
            user_preferences = await self._get_user_response_preferences(session, user_id)
            
            # Build context from multiple sources
            context = await self._build_comprehensive_context(
                session, user_id, query, conversation_id, include_team_context
            )
            
            # Generate personalized response structure
            response_structure = await self._determine_response_structure(
                user_preferences, query, context, response_format
            )
            
            # Create follow-up suggestions
            follow_up_suggestions = await self._generate_follow_up_suggestions(
                session, user_id, query, context
            )
            
            # Generate proactive insights
            proactive_insights = await self._generate_proactive_insights(
                session, user_id, context
            )
            
            return {
                "user_id": user_id,
                "query": query,
                "context": context,
                "response_structure": response_structure,
                "follow_up_suggestions": follow_up_suggestions,
                "proactive_insights": proactive_insights,
                "personalization_applied": user_preferences,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating contextualized response: {e}")
            raise
        finally:
            if not self.session:
                await session.close()
    
    async def _get_user_response_preferences(
        self,
        session: AsyncSession,
        user_id: str
    ) -> Dict[str, Any]:
        """Get user preferences for response personalization."""
        # Get communication style preferences
        comm_prefs_query = select(UserPreference).where(
            and_(
                UserPreference.user_id == user_id,
                UserPreference.preference_category == "communication_style",
                UserPreference.is_active == True
            )
        )
        comm_prefs_result = await session.execute(comm_prefs_query)
        comm_prefs = comm_prefs_result.scalars().all()
        
        # Get format preferences
        format_prefs_query = select(UserPreference).where(
            and_(
                UserPreference.user_id == user_id,
                UserPreference.preference_category == "format_preference",
                UserPreference.is_active == True
            )
        )
        format_prefs_result = await session.execute(format_prefs_query)
        format_prefs = format_prefs_result.scalars().all()
        
        # Organize preferences
        preferences = {
            "communication_style": {},
            "format_preferences": {},
            "confidence_levels": {}
        }
        
        for pref in comm_prefs:
            if pref.confidence_score >= 0.5:  # Only use confident preferences
                preferences["communication_style"][pref.preference_key] = pref.preference_value
                preferences["confidence_levels"][pref.preference_key] = pref.confidence_score
        
        for pref in format_prefs:
            if pref.confidence_score >= 0.5:
                preferences["format_preferences"][pref.preference_key] = pref.preference_value
                preferences["confidence_levels"][pref.preference_key] = pref.confidence_score
        
        return preferences
    
    async def _build_comprehensive_context(
        self,
        session: AsyncSession,
        user_id: str,
        query: str,
        conversation_id: Optional[str],
        include_team_context: bool
    ) -> Dict[str, Any]:
        """Build comprehensive context from multiple sources."""
        context = {
            "query_context": await self._analyze_query_context(query),
            "conversation_context": await self._get_conversation_context(session, conversation_id) if conversation_id else {},
            "user_memory_context": await self._get_relevant_user_memories(session, user_id, query),
            "team_context": await self._get_relevant_team_context(session, user_id, query) if include_team_context else {},
            "historical_patterns": await self._get_user_interaction_patterns(session, user_id, query),
            "recent_decisions": await self._get_recent_decisions(session, user_id),
            "topic_preferences": await self._get_topic_preferences(session, user_id, query)
        }
        
        return context
    
    async def _analyze_query_context(self, query: str) -> Dict[str, Any]:
        """Analyze the query to understand intent and context."""
        query_lower = query.lower()
        
        # Detect query type
        question_words = ["what", "how", "why", "when", "where", "who"]
        is_question = any(word in query_lower for word in question_words) or query.strip().endswith("?")
        
        # Detect urgency indicators
        urgent_words = ["urgent", "asap", "immediately", "quickly", "emergency", "critical"]
        urgency_level = "high" if any(word in query_lower for word in urgent_words) else "normal"
        
        # Detect topic categories
        topic_keywords = {
            "project_management": ["project", "deadline", "milestone", "task", "schedule"],
            "team_performance": ["team", "performance", "productivity", "metrics"],
            "technical": ["technical", "code", "development", "bug", "feature"],
            "business": ["revenue", "sales", "customer", "market", "strategy"],
            "operational": ["process", "workflow", "efficiency", "optimization"]
        }
        
        detected_topics = []
        for topic, keywords in topic_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_topics.append(topic)
        
        # Analyze complexity
        word_count = len(query.split())
        complexity = "high" if word_count > 20 else "medium" if word_count > 10 else "low"
        
        return {
            "is_question": is_question,
            "urgency_level": urgency_level,
            "detected_topics": detected_topics,
            "complexity": complexity,
            "word_count": word_count,
            "query_length": len(query)
        }
    
    async def _get_conversation_context(
        self,
        session: AsyncSession,
        conversation_id: str
    ) -> Dict[str, Any]:
        """Get context from the current conversation."""
        conv_query = select(Conversation).options(
            selectinload(Conversation.messages)
        ).where(Conversation.id == conversation_id)
        
        conv_result = await session.execute(conv_query)
        conversation = conv_result.scalar_one_or_none()
        
        if not conversation:
            return {}
        
        # Analyze recent messages for context
        recent_messages = sorted(conversation.messages, key=lambda m: m.sequence_number)[-10:]
        
        conversation_topics = []
        user_questions = []
        ai_responses = []
        
        for msg in recent_messages:
            if msg.message_type == "user_query":
                user_questions.append(msg.content)
                # Extract topics from user messages
                conversation_topics.extend(self._extract_topics_from_text(msg.content))
            elif msg.message_type == "ai_response":
                ai_responses.append(msg.content)
        
        return {
            "conversation_id": conversation_id,
            "context_type": conversation.context_type,
            "message_count": len(conversation.messages),
            "recent_topics": list(set(conversation_topics)),
            "recent_user_questions": user_questions[-3:],  # Last 3 questions
            "conversation_length": len(recent_messages),
            "last_activity": conversation.last_activity_at.isoformat() if conversation.last_activity_at else None
        }
    
    def _extract_topics_from_text(self, text: str) -> List[str]:
        """Extract topic keywords from text."""
        topic_patterns = {
            "deadline": r"\b(deadline|due date|timeline|schedule)\b",
            "meeting": r"\b(meeting|call|discussion|sync)\b",
            "project": r"\b(project|initiative|campaign)\b",
            "team": r"\b(team|colleague|member|staff)\b",
            "performance": r"\b(performance|metrics|kpi|results)\b",
            "issue": r"\b(issue|problem|bug|error)\b",
            "feature": r"\b(feature|enhancement|improvement)\b"
        }
        
        topics = []
        text_lower = text.lower()
        
        for topic, pattern in topic_patterns.items():
            if re.search(pattern, text_lower):
                topics.append(topic)
        
        return topics
    
    async def _get_relevant_user_memories(
        self,
        session: AsyncSession,
        user_id: str,
        query: str
    ) -> Dict[str, Any]:
        """Get relevant user memories based on query context."""
        # For now, get recent memories. In production, use semantic search
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.context_window_days)
        
        memories_query = select(UserMemory).where(
            and_(
                UserMemory.user_id == user_id,
                UserMemory.is_active == True,
                UserMemory.created_at >= cutoff_date,
                UserMemory.importance_score >= self.relevance_threshold
            )
        ).order_by(
            UserMemory.importance_score.desc(),
            UserMemory.created_at.desc()
        ).limit(self.max_context_memories)
        
        memories_result = await session.execute(memories_query)
        memories = memories_result.scalars().all()
        
        # Organize memories by type and category
        organized_memories = defaultdict(list)
        
        for memory in memories:
            memory_data = {
                "id": memory.id,
                "content": memory.content,
                "category": memory.category,
                "importance_score": memory.importance_score,
                "confidence_level": memory.confidence_level,
                "created_at": memory.created_at.isoformat()
            }
            organized_memories[memory.memory_type].append(memory_data)
        
        return {
            "total_memories": len(memories),
            "memories_by_type": dict(organized_memories),
            "avg_importance": sum(m.importance_score for m in memories) / max(len(memories), 1),
            "date_range": {
                "from": cutoff_date.isoformat(),
                "to": datetime.now(timezone.utc).isoformat()
            }
        }
    
    async def _get_relevant_team_context(
        self,
        session: AsyncSession,
        user_id: str,
        query: str
    ) -> Dict[str, Any]:
        """Get relevant team context and shared memories."""
        # Get user's teams
        from app.models.user import TeamMember
        
        teams_query = select(TeamMember.team_id).where(
            and_(
                TeamMember.user_id == user_id,
                TeamMember.is_active == True
            )
        )
        teams_result = await session.execute(teams_query)
        team_ids = [row[0] for row in teams_result.fetchall()]
        
        if not team_ids:
            return {}
        
        # Get relevant team memories
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.context_window_days)
        
        team_memories_query = select(TeamMemory).where(
            and_(
                TeamMemory.team_id.in_(team_ids),
                TeamMemory.is_active == True,
                TeamMemory.created_at >= cutoff_date,
                TeamMemory.relevance_score >= self.relevance_threshold
            )
        ).order_by(
            TeamMemory.relevance_score.desc(),
            TeamMemory.consensus_level.desc(),
            TeamMemory.created_at.desc()
        ).limit(10)
        
        team_memories_result = await session.execute(team_memories_query)
        team_memories = team_memories_result.scalars().all()
        
        # Organize team context
        team_context = {
            "team_count": len(team_ids),
            "relevant_memories": [],
            "recent_decisions": [],
            "team_knowledge": defaultdict(list)
        }
        
        for memory in team_memories:
            memory_data = {
                "id": memory.id,
                "title": memory.title,
                "memory_type": memory.memory_type,
                "category": memory.category,
                "relevance_score": memory.relevance_score,
                "consensus_level": memory.consensus_level,
                "created_at": memory.created_at.isoformat()
            }
            
            team_context["relevant_memories"].append(memory_data)
            team_context["team_knowledge"][memory.memory_type].append(memory_data)
        
        return team_context
    
    async def _get_user_interaction_patterns(
        self,
        session: AsyncSession,
        user_id: str,
        query: str
    ) -> Dict[str, Any]:
        """Get user interaction patterns relevant to the query."""
        patterns_query = select(UserBehaviorPattern).where(
            and_(
                UserBehaviorPattern.user_id == user_id,
                UserBehaviorPattern.is_active == True,
                UserBehaviorPattern.predictive_value >= 0.3
            )
        ).order_by(UserBehaviorPattern.predictive_value.desc()).limit(5)
        
        patterns_result = await session.execute(patterns_query)
        patterns = patterns_result.scalars().all()
        
        relevant_patterns = []
        for pattern in patterns:
            pattern_data = {
                "pattern_type": pattern.pattern_type,
                "pattern_name": pattern.pattern_name,
                "frequency_score": pattern.frequency_score,
                "consistency_score": pattern.consistency_score,
                "predictive_value": pattern.predictive_value,
                "pattern_data": pattern.pattern_data
            }
            relevant_patterns.append(pattern_data)
        
        return {
            "patterns_found": len(relevant_patterns),
            "patterns": relevant_patterns
        }
    
    async def _get_recent_decisions(
        self,
        session: AsyncSession,
        user_id: str
    ) -> Dict[str, Any]:
        """Get recent decisions relevant to current context."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=14)  # Last 2 weeks
        
        decisions_query = select(Decision).where(
            and_(
                Decision.user_id == user_id,
                Decision.decided_at >= cutoff_date
            )
        ).order_by(Decision.decided_at.desc()).limit(5)
        
        decisions_result = await session.execute(decisions_query)
        decisions = decisions_result.scalars().all()
        
        recent_decisions = []
        for decision in decisions:
            decision_data = {
                "id": decision.id,
                "title": decision.title,
                "decision_type": decision.decision_type,
                "status": decision.status,
                "priority_level": decision.priority_level,
                "decided_at": decision.decided_at.isoformat(),
                "context_tags": decision.context_tags
            }
            recent_decisions.append(decision_data)
        
        return {
            "recent_decisions_count": len(recent_decisions),
            "decisions": recent_decisions
        }
    
    async def _get_topic_preferences(
        self,
        session: AsyncSession,
        user_id: str,
        query: str
    ) -> Dict[str, Any]:
        """Get user topic preferences relevant to the query."""
        topic_prefs_query = select(UserPreference).where(
            and_(
                UserPreference.user_id == user_id,
                UserPreference.preference_category == "topic_interest",
                UserPreference.is_active == True,
                UserPreference.confidence_score >= 0.4
            )
        ).order_by(UserPreference.confidence_score.desc())
        
        topic_prefs_result = await session.execute(topic_prefs_query)
        topic_prefs = topic_prefs_result.scalars().all()
        
        preferences = {}
        for pref in topic_prefs:
            preferences[pref.preference_key] = {
                "value": pref.preference_value,
                "confidence": pref.confidence_score,
                "last_updated": pref.updated_at.isoformat()
            }
        
        return preferences
    
    async def _determine_response_structure(
        self,
        user_preferences: Dict[str, Any],
        query: str,
        context: Dict[str, Any],
        response_format: Optional[str]
    ) -> Dict[str, Any]:
        """Determine the optimal response structure based on preferences and context."""
        # Get communication style preferences
        comm_style = user_preferences.get("communication_style", {})
        format_prefs = user_preferences.get("format_preferences", {})
        
        # Determine response characteristics
        response_structure = {
            "tone": self._determine_tone(comm_style, context),
            "detail_level": self._determine_detail_level(comm_style, query, context),
            "format": self._determine_format(format_prefs, response_format, context),
            "length": self._determine_length(comm_style, query),
            "technical_depth": self._determine_technical_depth(comm_style, context),
            "personalization_elements": self._get_personalization_elements(user_preferences, context)
        }
        
        return response_structure
    
    def _determine_tone(self, comm_style: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Determine appropriate response tone."""
        # Check for urgency
        if context.get("query_context", {}).get("urgency_level") == "high":
            return "direct"
        
        # Use user preference if available
        tone_pref = comm_style.get("tone_preference", {})
        if isinstance(tone_pref, dict) and "tone_preference" in tone_pref:
            return tone_pref["tone_preference"]
        
        # Default to professional
        return "professional"
    
    def _determine_detail_level(
        self,
        comm_style: Dict[str, Any],
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """Determine appropriate level of detail."""
        # Check query complexity
        query_complexity = context.get("query_context", {}).get("complexity", "medium")
        
        if query_complexity == "high":
            return "detailed"
        
        # Use user preference for length
        length_pref = comm_style.get("response_length_preference", {})
        if isinstance(length_pref, dict) and "preferred_length" in length_pref:
            return length_pref["preferred_length"]
        
        return "medium"
    
    def _determine_format(
        self,
        format_prefs: Dict[str, Any],
        response_format: Optional[str],
        context: Dict[str, Any]
    ) -> str:
        """Determine response format."""
        # Use explicitly requested format
        if response_format:
            return response_format
        
        # Use user preferences
        if format_prefs:
            # Check for format preferences
            for key, value in format_prefs.items():
                if isinstance(value, dict) and "format" in value:
                    return value["format"]
        
        # Default based on query type
        if context.get("query_context", {}).get("is_question"):
            return "structured"
        
        return "conversational"
    
    def _determine_length(self, comm_style: Dict[str, Any], query: str) -> str:
        """Determine appropriate response length."""
        length_pref = comm_style.get("response_length_preference", {})
        if isinstance(length_pref, dict) and "preferred_length" in length_pref:
            return length_pref["preferred_length"]
        
        # Base on query length
        query_length = len(query.split())
        if query_length < 5:
            return "brief"
        elif query_length > 20:
            return "detailed"
        
        return "medium"
    
    def _determine_technical_depth(self, comm_style: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Determine appropriate technical depth."""
        tech_depth = comm_style.get("technical_depth_preference", {})
        if isinstance(tech_depth, dict) and "technical_depth" in tech_depth:
            return tech_depth["technical_depth"]
        
        # Check if technical topics are involved
        detected_topics = context.get("query_context", {}).get("detected_topics", [])
        if "technical" in detected_topics:
            return "advanced"
        
        return "medium"
    
    def _get_personalization_elements(
        self,
        user_preferences: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get elements for response personalization."""
        elements = {
            "include_historical_context": len(context.get("user_memory_context", {}).get("memories_by_type", {})) > 0,
            "reference_recent_decisions": len(context.get("recent_decisions", {}).get("decisions", [])) > 0,
            "acknowledge_patterns": len(context.get("historical_patterns", {}).get("patterns", [])) > 0,
            "include_team_context": len(context.get("team_context", {})) > 0,
            "confidence_indicators": user_preferences.get("confidence_levels", {}),
            "adaptation_suggestions": self._get_adaptation_suggestions(context)
        }
        
        return elements
    
    def _get_adaptation_suggestions(self, context: Dict[str, Any]) -> List[str]:
        """Get suggestions for adapting the response."""
        suggestions = []
        
        # Check if patterns suggest different approach
        patterns = context.get("historical_patterns", {}).get("patterns", [])
        for pattern in patterns:
            if pattern.get("predictive_value", 0) > 0.7:
                suggestions.append(f"Based on your {pattern['pattern_type']} pattern, consider...")
        
        # Check if team context suggests collaboration
        team_context = context.get("team_context", {})
        if team_context.get("relevant_memories"):
            suggestions.append("Your team has relevant experience with this topic")
        
        return suggestions
    
    async def _generate_follow_up_suggestions(
        self,
        session: AsyncSession,
        user_id: str,
        query: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate intelligent follow-up question suggestions."""
        suggestions = []
        
        # Based on query context
        query_context = context.get("query_context", {})
        detected_topics = query_context.get("detected_topics", [])
        
        # Topic-based suggestions
        topic_suggestions = {
            "project_management": [
                "What are the key milestones for this project?",
                "Who are the stakeholders involved?",
                "What are the potential risks?"
            ],
            "team_performance": [
                "What metrics are we tracking?",
                "How does this compare to previous periods?",
                "What actions should we take?"
            ],
            "technical": [
                "What are the technical requirements?",
                "Are there any dependencies?",
                "What's the implementation timeline?"
            ]
        }
        
        for topic in detected_topics:
            if topic in topic_suggestions:
                for suggestion in topic_suggestions[topic][:2]:  # Limit to 2 per topic
                    suggestions.append({
                        "question": suggestion,
                        "category": topic,
                        "relevance": "high"
                    })
        
        # Based on user patterns
        patterns = context.get("historical_patterns", {}).get("patterns", [])
        for pattern in patterns[:2]:  # Top 2 patterns
            if pattern.get("predictive_value", 0) > 0.5:
                suggestions.append({
                    "question": f"Would you like insights about your {pattern['pattern_name']}?",
                    "category": "pattern_based",
                    "relevance": "medium"
                })
        
        # Based on team context
        team_memories = context.get("team_context", {}).get("relevant_memories", [])
        if team_memories:
            suggestions.append({
                "question": "What has the team learned about this topic?",
                "category": "team_context",
                "relevance": "high"
            })
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    async def _generate_proactive_insights(
        self,
        session: AsyncSession,
        user_id: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate proactive insights based on context and patterns."""
        insights = []
        
        # Pattern-based insights
        patterns = context.get("historical_patterns", {}).get("patterns", [])
        for pattern in patterns:
            if pattern.get("predictive_value", 0) > 0.6:
                insights.append({
                    "type": "pattern_insight",
                    "title": f"Pattern Detected: {pattern['pattern_name']}",
                    "description": f"Based on your {pattern['pattern_type']} pattern, you typically...",
                    "confidence": pattern["predictive_value"],
                    "category": "behavioral"
                })
        
        # Decision context insights
        recent_decisions = context.get("recent_decisions", {}).get("decisions", [])
        pending_decisions = [d for d in recent_decisions if d["status"] == "pending"]
        if pending_decisions:
            insights.append({
                "type": "decision_reminder",
                "title": f"Pending Decisions ({len(pending_decisions)})",
                "description": "You have pending decisions that may be relevant to this query",
                "confidence": 0.8,
                "category": "actionable"
            })
        
        # Team collaboration insights
        team_context = context.get("team_context", {})
        if team_context.get("relevant_memories"):
            high_consensus_memories = [
                m for m in team_context["relevant_memories"] 
                if m.get("consensus_level", 0) > 0.8
            ]
            if high_consensus_memories:
                insights.append({
                    "type": "team_knowledge",
                    "title": "Team Consensus Available",
                    "description": f"Your team has high consensus on {len(high_consensus_memories)} related topics",
                    "confidence": 0.9,
                    "category": "collaborative"
                })
        
        # Memory-based insights
        user_memories = context.get("user_memory_context", {}).get("memories_by_type", {})
        if "context" in user_memories:
            context_memories = user_memories["context"]
            if len(context_memories) > 3:
                insights.append({
                    "type": "historical_context",
                    "title": "Rich Historical Context Available",
                    "description": f"You have {len(context_memories)} related memories that might provide additional context",
                    "confidence": 0.7,
                    "category": "informational"
                })
        
        return insights[:3]  # Limit to 3 insights
    
    async def apply_response_formatting(
        self,
        response_content: str,
        response_structure: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply formatting to response based on user preferences."""
        formatted_response = {
            "content": response_content,
            "format": response_structure.get("format", "conversational"),
            "tone": response_structure.get("tone", "professional"),
            "detail_level": response_structure.get("detail_level", "medium"),
            "technical_depth": response_structure.get("technical_depth", "medium"),
            "personalization_applied": response_structure.get("personalization_elements", {}),
            "formatting_metadata": {
                "response_length": len(response_content),
                "word_count": len(response_content.split()),
                "estimated_reading_time": len(response_content.split()) // 200  # ~200 WPM
            }
        }
        
        # Apply format-specific transformations
        if response_structure.get("format") == "structured":
            formatted_response["structured_content"] = self._create_structured_format(response_content)
        elif response_structure.get("format") == "bullet_points":
            formatted_response["bullet_points"] = self._create_bullet_format(response_content)
        
        return formatted_response
    
    def _create_structured_format(self, content: str) -> Dict[str, Any]:
        """Create structured format for response."""
        # Simple implementation - in production, use more sophisticated parsing
        sections = content.split("\n\n")
        
        structured = {
            "summary": sections[0] if sections else content[:200] + "...",
            "main_content": sections[1:] if len(sections) > 1 else [content],
            "key_points": self._extract_key_points(content)
        }
        
        return structured
    
    def _create_bullet_format(self, content: str) -> List[str]:
        """Create bullet point format for response."""
        # Simple implementation - extract sentences as bullet points
        sentences = [s.strip() for s in content.split(".") if s.strip()]
        return sentences[:5]  # Limit to 5 bullet points
    
    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from content."""
        # Simple implementation - look for sentences with key indicators
        key_indicators = ["important", "key", "main", "primary", "essential", "critical"]
        sentences = [s.strip() for s in content.split(".") if s.strip()]
        
        key_points = []
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in key_indicators):
                key_points.append(sentence)
        
        return key_points[:3]  # Limit to 3 key points


# Singleton instance for easy access
context_response_service = ContextAwareResponseService()