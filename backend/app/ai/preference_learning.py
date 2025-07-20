"""User Preference Learning Service for SingleBrief.

This module implements the user preference learning system that tracks
communication styles, topic interests, and behavioral patterns to
personalize AI responses and content delivery.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
import statistics
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.memory import UserPreference, UserBehaviorPattern, ConversationMessage, Conversation
from app.models.user import User
from app.core.database import get_async_session

logger = logging.getLogger(__name__)


class PreferenceLearningService:
    """Service for learning and managing user preferences."""
    
    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
        self.min_evidence_count = 3  # Minimum evidence points to establish preference
        self.confidence_threshold = 0.7  # Threshold for acting on preferences
        self.pattern_window_days = 30  # Days to look back for pattern analysis
        
    async def analyze_communication_style(self, user_id: str) -> Dict[str, Any]:
        """Analyze user's communication style from conversation history.
        
        Args:
            user_id: ID of the user to analyze
            
        Returns:
            Dict containing communication style preferences
        """
        session = self.session or await get_async_session().__anext__()
        
        try:
            # Get recent conversations for analysis
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.pattern_window_days)
            
            query = select(ConversationMessage).join(Conversation).where(
                and_(
                    Conversation.user_id == user_id,
                    ConversationMessage.message_type == "user_query",
                    ConversationMessage.created_at >= cutoff_date
                )
            ).options(selectinload(ConversationMessage.conversation))
            
            result = await session.execute(query)
            messages = result.scalars().all()
            
            if not messages:
                return {"status": "insufficient_data", "message_count": 0}
            
            # Analyze communication patterns
            style_analysis = {
                "formality_level": self._analyze_formality(messages),
                "response_length_preference": self._analyze_length_preference(messages),
                "technical_depth_preference": self._analyze_technical_depth(messages),
                "question_style": self._analyze_question_style(messages),
                "urgency_patterns": self._analyze_urgency_patterns(messages),
                "tone_preference": self._analyze_tone_preference(messages)
            }
            
            # Update or create communication style preferences
            await self._update_communication_preferences(session, user_id, style_analysis)
            
            return {
                "status": "success",
                "message_count": len(messages),
                "analysis": style_analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing communication style for user {user_id}: {e}")
            raise
        finally:
            if not self.session:
                await session.close()
    
    def _analyze_formality(self, messages: List[ConversationMessage]) -> Dict[str, Any]:
        """Analyze formality level from message content."""
        formal_indicators = ["please", "thank you", "would you", "could you", "i would like"]
        informal_indicators = ["hey", "thanks", "thx", "can you", "show me", "gimme"]
        
        formal_count = 0
        informal_count = 0
        
        for message in messages:
            content_lower = message.content.lower()
            formal_count += sum(1 for indicator in formal_indicators if indicator in content_lower)
            informal_count += sum(1 for indicator in informal_indicators if indicator in content_lower)
        
        total_indicators = formal_count + informal_count
        if total_indicators == 0:
            formality_score = 0.5  # Neutral
        else:
            formality_score = formal_count / total_indicators
        
        return {
            "formality_score": formality_score,
            "formal_indicators": formal_count,
            "informal_indicators": informal_count,
            "confidence": min(total_indicators / 10, 1.0)  # Max confidence at 10+ indicators
        }
    
    def _analyze_length_preference(self, messages: List[ConversationMessage]) -> Dict[str, Any]:
        """Analyze preferred response length from query patterns."""
        lengths = [len(message.content.split()) for message in messages]
        
        if not lengths:
            return {"preferred_length": "medium", "confidence": 0.0}
        
        avg_length = statistics.mean(lengths)
        median_length = statistics.median(lengths)
        
        # Classify preference based on average query length
        if avg_length < 10:
            length_pref = "brief"
        elif avg_length < 25:
            length_pref = "medium"
        else:
            length_pref = "detailed"
        
        return {
            "preferred_length": length_pref,
            "average_query_length": avg_length,
            "median_query_length": median_length,
            "confidence": min(len(lengths) / 20, 1.0)  # Max confidence at 20+ messages
        }
    
    def _analyze_technical_depth(self, messages: List[ConversationMessage]) -> Dict[str, Any]:
        """Analyze preferred technical depth from query complexity."""
        technical_terms = [
            "api", "database", "algorithm", "implementation", "architecture",
            "scalability", "performance", "optimization", "integration", "deployment"
        ]
        
        technical_scores = []
        for message in messages:
            content_lower = message.content.lower()
            tech_count = sum(1 for term in technical_terms if term in content_lower)
            word_count = len(message.content.split())
            tech_ratio = tech_count / max(word_count, 1)
            technical_scores.append(tech_ratio)
        
        if not technical_scores:
            return {"technical_depth": "medium", "confidence": 0.0}
        
        avg_tech_ratio = statistics.mean(technical_scores)
        
        if avg_tech_ratio < 0.05:
            depth_pref = "basic"
        elif avg_tech_ratio < 0.15:
            depth_pref = "medium"
        else:
            depth_pref = "advanced"
        
        return {
            "technical_depth": depth_pref,
            "average_technical_ratio": avg_tech_ratio,
            "confidence": min(len(messages) / 15, 1.0)
        }
    
    def _analyze_question_style(self, messages: List[ConversationMessage]) -> Dict[str, Any]:
        """Analyze question asking patterns and style."""
        question_count = 0
        direct_questions = 0
        open_questions = 0
        
        for message in messages:
            content = message.content.strip()
            if content.endswith("?"):
                question_count += 1
                if any(word in content.lower() for word in ["what", "how", "why", "when", "where"]):
                    open_questions += 1
                else:
                    direct_questions += 1
        
        total_messages = len(messages)
        question_ratio = question_count / max(total_messages, 1)
        
        if question_count > 0:
            open_ratio = open_questions / question_count
        else:
            open_ratio = 0.5
        
        style = "exploratory" if open_ratio > 0.6 else "direct" if open_ratio < 0.4 else "balanced"
        
        return {
            "question_style": style,
            "question_ratio": question_ratio,
            "open_question_ratio": open_ratio,
            "confidence": min(question_count / 10, 1.0)
        }
    
    def _analyze_urgency_patterns(self, messages: List[ConversationMessage]) -> Dict[str, Any]:
        """Analyze urgency indicators in user messages."""
        urgency_words = ["urgent", "asap", "immediately", "quickly", "fast", "rush", "emergency"]
        time_words = ["today", "now", "right now", "this morning", "this afternoon"]
        
        urgent_messages = 0
        for message in messages:
            content_lower = message.content.lower()
            if any(word in content_lower for word in urgency_words + time_words):
                urgent_messages += 1
        
        urgency_ratio = urgent_messages / max(len(messages), 1)
        
        if urgency_ratio > 0.3:
            urgency_level = "high"
        elif urgency_ratio > 0.1:
            urgency_level = "medium"
        else:
            urgency_level = "low"
        
        return {
            "urgency_level": urgency_level,
            "urgency_ratio": urgency_ratio,
            "confidence": min(len(messages) / 20, 1.0)
        }
    
    def _analyze_tone_preference(self, messages: List[ConversationMessage]) -> Dict[str, Any]:
        """Analyze preferred communication tone from user messages."""
        positive_words = ["please", "thank you", "thanks", "appreciate", "great", "excellent"]
        casual_words = ["hey", "hi", "cool", "awesome", "sweet", "nice"]
        direct_words = ["need", "want", "show", "give", "tell", "explain"]
        
        positive_count = 0
        casual_count = 0
        direct_count = 0
        
        for message in messages:
            content_lower = message.content.lower()
            positive_count += sum(1 for word in positive_words if word in content_lower)
            casual_count += sum(1 for word in casual_words if word in content_lower)
            direct_count += sum(1 for word in direct_words if word in content_lower)
        
        total_indicators = positive_count + casual_count + direct_count
        
        if total_indicators == 0:
            tone_pref = "neutral"
            confidence = 0.0
        else:
            if positive_count > casual_count and positive_count > direct_count:
                tone_pref = "polite"
            elif casual_count > direct_count:
                tone_pref = "casual"
            else:
                tone_pref = "direct"
            confidence = min(total_indicators / 15, 1.0)
        
        return {
            "tone_preference": tone_pref,
            "positive_indicators": positive_count,
            "casual_indicators": casual_count,
            "direct_indicators": direct_count,
            "confidence": confidence
        }
    
    async def _update_communication_preferences(
        self, 
        session: AsyncSession, 
        user_id: str, 
        analysis: Dict[str, Any]
    ) -> None:
        """Update communication style preferences in database."""
        try:
            # Get user's organization_id
            user_query = select(User).where(User.id == user_id)
            user_result = await session.execute(user_query)
            user = user_result.scalar_one()
            
            for style_key, style_data in analysis.items():
                if isinstance(style_data, dict) and "confidence" in style_data:
                    confidence = style_data["confidence"]
                    
                    # Only update if confidence is reasonable
                    if confidence >= 0.3:
                        await self._upsert_preference(
                            session=session,
                            user_id=user_id,
                            organization_id=user.organization_id,
                            category="communication_style",
                            key=style_key,
                            value=style_data,
                            confidence=confidence,
                            source="behavioral_analysis"
                        )
            
            await session.commit()
            
        except Exception as e:
            logger.error(f"Error updating communication preferences: {e}")
            await session.rollback()
            raise
    
    async def analyze_topic_interests(self, user_id: str) -> Dict[str, Any]:
        """Analyze user topic interests and engagement patterns.
        
        Args:
            user_id: ID of the user to analyze
            
        Returns:
            Dict containing topic interest analysis
        """
        session = self.session or await get_async_session().__anext__()
        
        try:
            # Get recent conversations for topic analysis
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.pattern_window_days)
            
            query = select(ConversationMessage).join(Conversation).where(
                and_(
                    Conversation.user_id == user_id,
                    ConversationMessage.message_type == "user_query",
                    ConversationMessage.created_at >= cutoff_date
                )
            ).options(selectinload(ConversationMessage.conversation))
            
            result = await session.execute(query)
            messages = result.scalars().all()
            
            if not messages:
                return {"status": "insufficient_data", "message_count": 0}
            
            # Analyze topic patterns
            topic_analysis = self._extract_topics_from_messages(messages)
            engagement_analysis = self._analyze_topic_engagement(messages)
            
            # Combine analyses
            combined_analysis = {
                "topic_frequencies": topic_analysis,
                "engagement_patterns": engagement_analysis,
                "message_count": len(messages)
            }
            
            # Update topic interest preferences
            await self._update_topic_preferences(session, user_id, combined_analysis)
            
            return {
                "status": "success",
                "analysis": combined_analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing topic interests for user {user_id}: {e}")
            raise
        finally:
            if not self.session:
                await session.close()
    
    def _extract_topics_from_messages(self, messages: List[ConversationMessage]) -> Dict[str, int]:
        """Extract topic keywords from conversation messages."""
        topic_keywords = {
            "project_management": ["project", "deadline", "milestone", "task", "planning", "roadmap"],
            "team_performance": ["team", "performance", "productivity", "metrics", "kpi", "goals"],
            "technical_architecture": ["architecture", "system", "design", "scalability", "infrastructure"],
            "data_analysis": ["data", "analytics", "reporting", "insights", "metrics", "trends"],
            "customer_feedback": ["customer", "feedback", "satisfaction", "review", "complaint"],
            "product_development": ["product", "feature", "development", "release", "iteration"],
            "financial_metrics": ["revenue", "cost", "budget", "profit", "financial", "expense"],
            "marketing_campaigns": ["marketing", "campaign", "brand", "awareness", "conversion"],
            "operational_efficiency": ["process", "efficiency", "optimization", "workflow", "automation"],
            "strategic_planning": ["strategy", "vision", "objectives", "planning", "roadmap", "growth"]
        }
        
        topic_counts = defaultdict(int)
        
        for message in messages:
            content_lower = message.content.lower()
            for topic, keywords in topic_keywords.items():
                for keyword in keywords:
                    if keyword in content_lower:
                        topic_counts[topic] += 1
                        break  # Count each message only once per topic
        
        return dict(topic_counts)
    
    def _analyze_topic_engagement(self, messages: List[ConversationMessage]) -> Dict[str, Any]:
        """Analyze user engagement patterns with different topics."""
        # Analyze message lengths by topic context
        # Analyze follow-up question patterns
        # Analyze time spent on different topic conversations
        
        engagement_metrics = {
            "average_message_length": statistics.mean([len(msg.content.split()) for msg in messages]),
            "question_frequency": sum(1 for msg in messages if msg.content.strip().endswith("?")) / len(messages),
            "conversation_depth": self._calculate_conversation_depth(messages)
        }
        
        return engagement_metrics
    
    def _calculate_conversation_depth(self, messages: List[ConversationMessage]) -> float:
        """Calculate average conversation depth (follow-up messages)."""
        conversation_lengths = defaultdict(int)
        
        for message in messages:
            conversation_lengths[message.conversation_id] += 1
        
        if conversation_lengths:
            return statistics.mean(list(conversation_lengths.values()))
        return 0.0
    
    async def _update_topic_preferences(
        self, 
        session: AsyncSession, 
        user_id: str, 
        analysis: Dict[str, Any]
    ) -> None:
        """Update topic interest preferences in database."""
        try:
            # Get user's organization_id
            user_query = select(User).where(User.id == user_id)
            user_result = await session.execute(user_query)
            user = user_result.scalar_one()
            
            # Update topic frequency preferences
            topic_frequencies = analysis.get("topic_frequencies", {})
            total_mentions = sum(topic_frequencies.values())
            
            if total_mentions > 0:
                for topic, count in topic_frequencies.items():
                    interest_score = count / total_mentions
                    confidence = min(count / 5, 1.0)  # Max confidence at 5+ mentions
                    
                    if confidence >= 0.2:  # Only store topics with reasonable evidence
                        await self._upsert_preference(
                            session=session,
                            user_id=user_id,
                            organization_id=user.organization_id,
                            category="topic_interest",
                            key=topic,
                            value={
                                "interest_score": interest_score,
                                "mention_count": count,
                                "total_mentions": total_mentions
                            },
                            confidence=confidence,
                            source="behavioral_analysis"
                        )
            
            # Update engagement pattern preferences
            engagement = analysis.get("engagement_patterns", {})
            if engagement:
                await self._upsert_preference(
                    session=session,
                    user_id=user_id,
                    organization_id=user.organization_id,
                    category="topic_interest",
                    key="engagement_patterns",
                    value=engagement,
                    confidence=0.8,
                    source="behavioral_analysis"
                )
            
            await session.commit()
            
        except Exception as e:
            logger.error(f"Error updating topic preferences: {e}")
            await session.rollback()
            raise
    
    async def _upsert_preference(
        self,
        session: AsyncSession,
        user_id: str,
        organization_id: str,
        category: str,
        key: str,
        value: Any,
        confidence: float,
        source: str
    ) -> None:
        """Insert or update a user preference."""
        # Check if preference exists
        query = select(UserPreference).where(
            and_(
                UserPreference.user_id == user_id,
                UserPreference.preference_category == category,
                UserPreference.preference_key == key
            )
        )
        result = await session.execute(query)
        existing_pref = result.scalar_one_or_none()
        
        if existing_pref:
            # Update existing preference with new evidence
            existing_pref.preference_value = value
            existing_pref.confidence_score = max(existing_pref.confidence_score, confidence)
            existing_pref.evidence_count += 1
            existing_pref.last_evidence_at = datetime.now(timezone.utc)
            existing_pref.updated_at = datetime.now(timezone.utc)
            
            # Update stability score based on consistency
            if existing_pref.evidence_count > 3:
                existing_pref.stability_score = min(existing_pref.stability_score + 0.1, 1.0)
        else:
            # Create new preference
            new_pref = UserPreference(
                user_id=user_id,
                organization_id=organization_id,
                preference_category=category,
                preference_key=key,
                preference_value=value,
                confidence_score=confidence,
                learning_source=source,
                evidence_count=1,
                last_evidence_at=datetime.now(timezone.utc)
            )
            session.add(new_pref)
    
    async def get_user_preferences(
        self, 
        user_id: str, 
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user preferences by category or all preferences.
        
        Args:
            user_id: ID of the user
            category: Optional category filter
            
        Returns:
            Dict containing user preferences
        """
        session = self.session or await get_async_session().__anext__()
        
        try:
            query = select(UserPreference).where(UserPreference.user_id == user_id)
            
            if category:
                query = query.where(UserPreference.preference_category == category)
            
            query = query.where(UserPreference.is_active == True)
            
            result = await session.execute(query)
            preferences = result.scalars().all()
            
            # Organize preferences by category and key
            organized_prefs = defaultdict(dict)
            
            for pref in preferences:
                organized_prefs[pref.preference_category][pref.preference_key] = {
                    "value": pref.preference_value,
                    "confidence": pref.confidence_score,
                    "evidence_count": pref.evidence_count,
                    "last_updated": pref.updated_at.isoformat(),
                    "is_manually_set": pref.is_manually_set,
                    "stability": pref.stability_score
                }
            
            return dict(organized_prefs)
            
        except Exception as e:
            logger.error(f"Error getting user preferences for {user_id}: {e}")
            raise
        finally:
            if not self.session:
                await session.close()
    
    async def update_preference_manually(
        self,
        user_id: str,
        category: str,
        key: str,
        value: Any,
        organization_id: str
    ) -> None:
        """Manually update a user preference.
        
        Args:
            user_id: ID of the user
            category: Preference category
            key: Preference key
            value: Preference value
            organization_id: User's organization ID
        """
        session = self.session or await get_async_session().__anext__()
        
        try:
            await self._upsert_preference(
                session=session,
                user_id=user_id,
                organization_id=organization_id,
                category=category,
                key=key,
                value=value,
                confidence=1.0,  # Manual preferences have full confidence
                source="manual_override"
            )
            
            # Mark as manually set
            query = select(UserPreference).where(
                and_(
                    UserPreference.user_id == user_id,
                    UserPreference.preference_category == category,
                    UserPreference.preference_key == key
                )
            )
            result = await session.execute(query)
            pref = result.scalar_one()
            pref.is_manually_set = True
            
            await session.commit()
            
        except Exception as e:
            logger.error(f"Error manually updating preference: {e}")
            await session.rollback()
            raise
        finally:
            if not self.session:
                await session.close()
    
    async def run_preference_learning_analysis(self, user_id: str) -> Dict[str, Any]:
        """Run comprehensive preference learning analysis for a user.
        
        Args:
            user_id: ID of the user to analyze
            
        Returns:
            Dict containing complete preference analysis results
        """
        try:
            # Run parallel analyses
            communication_task = self.analyze_communication_style(user_id)
            topic_task = self.analyze_topic_interests(user_id)
            
            communication_results, topic_results = await asyncio.gather(
                communication_task, topic_task, return_exceptions=True
            )
            
            results = {
                "user_id": user_id,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "communication_style": communication_results if not isinstance(communication_results, Exception) else {"error": str(communication_results)},
                "topic_interests": topic_results if not isinstance(topic_results, Exception) else {"error": str(topic_results)}
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error running preference learning analysis for user {user_id}: {e}")
            raise


# Singleton instance for easy access
preference_learning_service = PreferenceLearningService()