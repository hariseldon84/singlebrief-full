"""Content Intelligence and Prioritization Service for SingleBrief.

This module provides advanced content analysis, importance scoring, urgency detection,
trend analysis, and intelligent content prioritization for brief generation.
"""

from typing import Any, Dict, List, Optional, Tuple

import logging
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum

from app.services.data_normalization import (ContentType, SourceType,
                                             UnifiedDataItem)

logger = logging.getLogger(__name__)

class ImportanceCategory(Enum):
    """Categories for content importance classification."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"

class UrgencyLevel(Enum):
    """Levels of urgency for content items."""

    IMMEDIATE = "immediate"
    TODAY = "today"
    THIS_WEEK = "this_week"
    SOON = "soon"
    NORMAL = "normal"

class TrendType(Enum):
    """Types of trends in content analysis."""

    EMERGING = "emerging"
    ESCALATING = "escalating"
    RECURRING = "recurring"
    DECLINING = "declining"
    STABLE = "stable"

@dataclass

class ContentIntelligence:
    """Intelligence analysis results for content items."""

    item_id: str
    importance_score: float
    importance_category: ImportanceCategory
    urgency_level: UrgencyLevel
    urgency_score: float
    trend_type: Optional[TrendType]
    trend_score: float
    action_items: List[str]
    risk_indicators: List[str]
    opportunity_indicators: List[str]
    key_topics: List[str]
    sentiment_score: float
    confidence_score: float
    reasoning: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "item_id": self.item_id,
            "importance_score": self.importance_score,
            "importance_category": self.importance_category.value,
            "urgency_level": self.urgency_level.value,
            "urgency_score": self.urgency_score,
            "trend_type": self.trend_type.value if self.trend_type else None,
            "trend_score": self.trend_score,
            "action_items": self.action_items,
            "risk_indicators": self.risk_indicators,
            "opportunity_indicators": self.opportunity_indicators,
            "key_topics": self.key_topics,
            "sentiment_score": self.sentiment_score,
            "confidence_score": self.confidence_score,
            "reasoning": self.reasoning,
        }

@dataclass

class TrendAnalysis:
    """Analysis of trends across content items."""

    topic: str
    trend_type: TrendType
    frequency: int
    velocity: float  # Change rate
    confidence: float
    related_items: List[str]
    time_span: timedelta

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "topic": self.topic,
            "trend_type": self.trend_type.value,
            "frequency": self.frequency,
            "velocity": self.velocity,
            "confidence": self.confidence,
            "related_items": self.related_items,
            "time_span_hours": self.time_span.total_seconds() / 3600,
        }

class ContentIntelligenceService:
    """Advanced content intelligence and prioritization service."""

    def __init__(self):
        # Importance keywords and weights
        self.critical_keywords = {
            "outage",
            "down",
            "broken",
            "critical",
            "emergency",
            "urgent",
            "severe",
            "security breach",
            "data loss",
            "system failure",
            "production issue",
        }

        self.high_importance_keywords = {
            "deadline",
            "milestone",
            "release",
            "launch",
            "meeting",
            "decision",
            "approval",
            "budget",
            "compliance",
            "audit",
            "legal",
            "contract",
        }

        self.urgency_patterns = {
            UrgencyLevel.IMMEDIATE: [
                r"asap",
                r"immediately",
                r"right now",
                r"urgent",
                r"emergency",
                r"critical",
                r"breaking",
                r"alert",
                r"failure",
                r"down",
            ],
            UrgencyLevel.TODAY: [
                r"today",
                r"by end of day",
                r"eod",
                r"before 5",
                r"this afternoon",
            ],
            UrgencyLevel.THIS_WEEK: [
                r"this week",
                r"by friday",
                r"end of week",
                r"weekly deadline",
            ],
            UrgencyLevel.SOON: [r"soon", r"upcoming", r"next week", r"in a few days"],
        }

        # Topic extraction patterns
        self.topic_patterns = {
            "project": r"\b(?:project|initiative|campaign)\s+([A-Za-z0-9\-_]+)",
            "system": r"\b(?:system|service|application)\s+([A-Za-z0-9\-_]+)",
            "person": r"@([A-Za-z0-9\-_]+)",
            "issue": r"(?:issue|bug|problem)\s+#?([A-Za-z0-9\-_]+)",
            "deadline": r"(?:deadline|due)\s+(.{1,20})",
            "meeting": r"(?:meeting|call)\s+(?:about|regarding)\s+(.{1,30})",
        }

        # Sentiment indicators
        self.positive_indicators = {
            "success",
            "completed",
            "achieved",
            "excellent",
            "great",
            "awesome",
            "perfect",
            "solved",
            "fixed",
            "resolved",
            "improved",
            "optimized",
        }

        self.negative_indicators = {
            "failed",
            "error",
            "problem",
            "issue",
            "broken",
            "delayed",
            "blocked",
            "concerned",
            "worried",
            "frustrated",
            "difficulty",
            "challenge",
        }

        # Risk indicators
        self.risk_keywords = {
            "technical": [
                "outage",
                "failure",
                "bug",
                "vulnerability",
                "breach",
                "crash",
            ],
            "schedule": ["delay", "behind", "overdue", "missed", "late", "postponed"],
            "resource": ["shortage", "unavailable", "overloaded", "capacity", "budget"],
            "quality": [
                "defect",
                "regression",
                "degradation",
                "performance",
                "stability",
            ],
            "compliance": ["violation", "audit", "regulation", "legal", "policy"],
        }

        # Opportunity indicators
        self.opportunity_keywords = {
            "efficiency": ["optimize", "streamline", "automate", "improve", "faster"],
            "growth": ["expand", "scale", "increase", "opportunity", "potential"],
            "innovation": ["new", "innovative", "creative", "breakthrough", "novel"],
            "cost_saving": ["reduce", "save", "cheaper", "efficient", "consolidate"],
        }

    async def analyze_content_intelligence(
        self, items: List[UnifiedDataItem], context: Optional[Dict[str, Any]] = None
    ) -> List[ContentIntelligence]:
        """Analyze content intelligence for a list of items."""
        try:
            intelligence_results = []

            # Analyze trends across all items first
            trend_analysis = await self._analyze_trends(items)

            for item in items:
                intelligence = await self._analyze_single_item(
                    item, items, trend_analysis, context
                )
                intelligence_results.append(intelligence)

            # Post-process for relative scoring
            intelligence_results = await self._normalize_scores(intelligence_results)

            logger.info(
                f"Analyzed intelligence for {len(intelligence_results)} content items"
            )
            return intelligence_results

        except Exception as e:
            logger.error(f"Error analyzing content intelligence: {e}")
            return []

    async def _analyze_single_item(
        self,
        item: UnifiedDataItem,
        all_items: List[UnifiedDataItem],
        trend_analysis: Dict[str, TrendAnalysis],
        context: Optional[Dict[str, Any]],
    ) -> ContentIntelligence:
        """Analyze intelligence for a single content item."""
        try:
            content_text = f"{item.title or ''} {item.content or ''}".lower()

            # Calculate importance score
            importance_score = await self._calculate_importance_score(
                item, all_items, context
            )
            importance_category = self._categorize_importance(importance_score)

            # Detect urgency
            urgency_level, urgency_score = await self._detect_urgency(item)

            # Analyze trends for this item
            item_topics = self._extract_topics(item)
            trend_type, trend_score = self._analyze_item_trends(
                item_topics, trend_analysis
            )

            # Extract action items
            action_items = await self._extract_action_items(item)

            # Detect risks and opportunities
            risk_indicators = self._detect_risks(item)
            opportunity_indicators = self._detect_opportunities(item)

            # Analyze sentiment
            sentiment_score = self._analyze_sentiment(item)

            # Calculate confidence
            confidence_score = self._calculate_confidence(
                item, importance_score, urgency_score
            )

            # Generate reasoning
            reasoning = self._generate_reasoning(
                item,
                importance_score,
                urgency_level,
                trend_type,
                len(action_items),
                len(risk_indicators),
                len(opportunity_indicators),
            )

            return ContentIntelligence(
                item_id=item.id,
                importance_score=importance_score,
                importance_category=importance_category,
                urgency_level=urgency_level,
                urgency_score=urgency_score,
                trend_type=trend_type,
                trend_score=trend_score,
                action_items=action_items,
                risk_indicators=risk_indicators,
                opportunity_indicators=opportunity_indicators,
                key_topics=item_topics,
                sentiment_score=sentiment_score,
                confidence_score=confidence_score,
                reasoning=reasoning,
            )

        except Exception as e:
            logger.error(f"Error analyzing single item intelligence: {e}")
            # Return minimal intelligence on error
            return ContentIntelligence(
                item_id=item.id,
                importance_score=0.5,
                importance_category=ImportanceCategory.MEDIUM,
                urgency_level=UrgencyLevel.NORMAL,
                urgency_score=0.0,
                trend_type=None,
                trend_score=0.0,
                action_items=[],
                risk_indicators=[],
                opportunity_indicators=[],
                key_topics=[],
                sentiment_score=0.0,
                confidence_score=0.3,
                reasoning="Error in analysis",
            )

    async def _calculate_importance_score(
        self,
        item: UnifiedDataItem,
        all_items: List[UnifiedDataItem],
        context: Optional[Dict[str, Any]],
    ) -> float:
        """Calculate multi-factor importance score."""
        try:
            score = 0.0
            content_text = f"{item.title or ''} {item.content or ''}".lower()

            # 1. Content type base score (0.0 - 0.3)
            content_type_scores = {
                ContentType.EMAIL: 0.25,
                ContentType.MESSAGE: 0.20,
                ContentType.ISSUE: 0.30,
                ContentType.PULL_REQUEST: 0.25,
                ContentType.DOCUMENT: 0.15,
                ContentType.CALENDAR_EVENT: 0.20,
                ContentType.REPOSITORY: 0.10,
                ContentType.PROJECT: 0.25,
            }
            score += content_type_scores.get(item.content_type, 0.15)

            # 2. Keyword-based importance (0.0 - 0.4)
            critical_matches = sum(
                1 for keyword in self.critical_keywords if keyword in content_text
            )
            high_matches = sum(
                1
                for keyword in self.high_importance_keywords
                if keyword in content_text
            )

            keyword_score = min(critical_matches * 0.15 + high_matches * 0.08, 0.4)
            score += keyword_score

            # 3. Author authority (0.0 - 0.2)
            author_score = self._calculate_author_authority(item, context)
            score += author_score

            # 4. Participant/audience size (0.0 - 0.15)
            participant_count = len(item.participants or [])
            audience_score = min(participant_count * 0.02, 0.15)
            score += audience_score

            # 5. Content quality and length (0.0 - 0.1)
            content_length = len(content_text)
            if content_length > 50:
                quality_score = min(0.05 + (content_length / 2000) * 0.05, 0.1)
                score += quality_score

            # 6. Recency bonus (0.0 - 0.1)
            if item.created_at:
                hours_old = (
                    datetime.now(timezone.utc) - item.created_at
                ).total_seconds() / 3600
                recency_score = max(
                    0, 0.1 - (hours_old / 168) * 0.1
                )  # Decay over a week
                score += recency_score

            # 7. Category-based importance (0.0 - 0.15)
            important_categories = {
                "action_item": 0.1,
                "technical_issue": 0.15,
                "meeting": 0.08,
                "project_management": 0.1,
                "urgent": 0.15,
            }

            for category in item.categories or []:
                if category in important_categories:
                    score += important_categories[category]
                    break  # Only count the highest category

            # 8. Cross-reference importance (0.0 - 0.1)
            if self._is_referenced_by_others(item, all_items):
                score += 0.1

            return min(score, 1.0)

        except Exception as e:
            logger.error(f"Error calculating importance score: {e}")
            return 0.5

    def _calculate_author_authority(
        self, item: UnifiedDataItem, context: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate author authority score."""
        try:
            if not item.author:
                return 0.0

            author_lower = item.author.lower()

            # Executive level
            if any(
                title in author_lower
                for title in ["ceo", "cto", "cfo", "vp", "president"]
            ):
                return 0.2

            # Management level
            if any(
                title in author_lower
                for title in ["director", "manager", "lead", "head"]
            ):
                return 0.15

            # Senior level
            if any(title in author_lower for title in ["senior", "principal", "staff"]):
                return 0.1

            # Context-based authority (if organization chart data available)
            if context and "authority_scores" in context:
                authority_scores = context["authority_scores"]
                return authority_scores.get(item.author, 0.05)

            return 0.05  # Default score for regular employees

        except Exception as e:
            logger.error(f"Error calculating author authority: {e}")
            return 0.05

    def _is_referenced_by_others(
        self, item: UnifiedDataItem, all_items: List[UnifiedDataItem]
    ) -> bool:
        """Check if item is referenced by other items."""
        try:
            item_keywords = set(
                self._extract_keywords(f"{item.title or ''} {item.content or ''}")
            )

            reference_count = 0
            for other_item in all_items:
                if other_item.id == item.id:
                    continue

                other_text = (
                    f"{other_item.title or ''} {other_item.content or ''}".lower()
                )
                other_keywords = set(self._extract_keywords(other_text))

                # Check for keyword overlap
                if len(item_keywords & other_keywords) >= 2:
                    reference_count += 1

                # Check for direct mentions
                if item.title and item.title.lower() in other_text:
                    reference_count += 1

            return reference_count >= 2

        except Exception as e:
            logger.error(f"Error checking cross-references: {e}")
            return False

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        import re

        # Clean and tokenize
        text = re.sub(r"[^\w\s]", " ", text.lower())
        words = text.split()

        # Filter out stop words and short words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "this",
            "that",
            "these",
            "those",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "me",
            "him",
            "her",
            "us",
            "them",
            "my",
            "your",
            "his",
            "its",
        }

        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        return keywords[:15]  # Return top 15 keywords

    def _categorize_importance(self, score: float) -> ImportanceCategory:
        """Categorize importance score into levels."""
        if score >= 0.85:
            return ImportanceCategory.CRITICAL
        elif score >= 0.7:
            return ImportanceCategory.HIGH
        elif score >= 0.5:
            return ImportanceCategory.MEDIUM
        elif score >= 0.3:
            return ImportanceCategory.LOW
        else:
            return ImportanceCategory.MINIMAL

    async def _detect_urgency(
        self, item: UnifiedDataItem
    ) -> Tuple[UrgencyLevel, float]:
        """Detect urgency level and score."""
        try:
            content_text = f"{item.title or ''} {item.content or ''}".lower()
            urgency_score = 0.0
            detected_level = UrgencyLevel.NORMAL

            # Pattern-based urgency detection
            for level, patterns in self.urgency_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, content_text):
                        if level == UrgencyLevel.IMMEDIATE:
                            urgency_score = max(urgency_score, 1.0)
                            detected_level = level
                        elif level == UrgencyLevel.TODAY:
                            urgency_score = max(urgency_score, 0.8)
                            if detected_level == UrgencyLevel.NORMAL:
                                detected_level = level
                        elif level == UrgencyLevel.THIS_WEEK:
                            urgency_score = max(urgency_score, 0.6)
                            if detected_level == UrgencyLevel.NORMAL:
                                detected_level = level
                        elif level == UrgencyLevel.SOON:
                            urgency_score = max(urgency_score, 0.4)
                            if detected_level == UrgencyLevel.NORMAL:
                                detected_level = level

            # Time-based urgency (deadlines)
            deadline_urgency = self._detect_deadline_urgency(content_text)
            if deadline_urgency > urgency_score:
                urgency_score = deadline_urgency
                if deadline_urgency >= 0.8:
                    detected_level = UrgencyLevel.TODAY
                elif deadline_urgency >= 0.6:
                    detected_level = UrgencyLevel.THIS_WEEK

            # Category-based urgency
            if any(
                cat in ["technical_issue", "urgent"] for cat in (item.categories or [])
            ):
                urgency_score = max(urgency_score, 0.7)
                if detected_level == UrgencyLevel.NORMAL:
                    detected_level = UrgencyLevel.TODAY

            # Source-based urgency (e.g., alerts from monitoring systems)
            if item.source_type in [SourceType.SLACK] and any(
                word in content_text for word in ["alert", "notification", "warning"]
            ):
                urgency_score = max(urgency_score, 0.6)

            return detected_level, urgency_score

        except Exception as e:
            logger.error(f"Error detecting urgency: {e}")
            return UrgencyLevel.NORMAL, 0.0

    def _detect_deadline_urgency(self, content_text: str) -> float:
        """Detect deadline-based urgency."""
        try:
            # Look for date/time patterns
            import re

            # Today patterns
            if re.search(
                r"\b(?:today|this afternoon|by end of day|eod)\b", content_text
            ):
                return 0.9

            # Tomorrow patterns
            if re.search(r"\b(?:tomorrow|by tomorrow)\b", content_text):
                return 0.7

            # This week patterns
            if re.search(r"\b(?:this week|by friday|end of week)\b", content_text):
                return 0.5

            # Next week patterns
            if re.search(r"\b(?:next week|early next week)\b", content_text):
                return 0.3

            return 0.0

        except Exception as e:
            logger.error(f"Error detecting deadline urgency: {e}")
            return 0.0

    def _extract_topics(self, item: UnifiedDataItem) -> List[str]:
        """Extract key topics from content."""
        try:
            content_text = f"{item.title or ''} {item.content or ''}"
            topics = []

            # Extract using predefined patterns
            for topic_type, pattern in self.topic_patterns.items():
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        topics.extend([m.strip() for m in match if m.strip()])
                    else:
                        topics.append(match.strip())

            # Add tags and categories as topics
            topics.extend(item.tags or [])
            topics.extend(item.categories or [])

            # Clean and deduplicate
            cleaned_topics = []
            for topic in topics:
                topic = topic.lower().strip()
                if len(topic) > 2 and topic not in cleaned_topics:
                    cleaned_topics.append(topic)

            return cleaned_topics[:10]  # Return top 10 topics

        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            return []

    async def _analyze_trends(
        self, items: List[UnifiedDataItem]
    ) -> Dict[str, TrendAnalysis]:
        """Analyze trends across all content items."""
        try:
            # Extract all topics and their timestamps
            topic_timeline = defaultdict(list)

            for item in items:
                topics = self._extract_topics(item)
                timestamp = (
                    item.updated_at or item.created_at or datetime.now(timezone.utc)
                )

                for topic in topics:
                    topic_timeline[topic].append(timestamp)

            # Analyze trends for each topic
            trend_analyses = {}

            for topic, timestamps in topic_timeline.items():
                if (
                    len(timestamps) < 2
                ):  # Need at least 2 occurrences for trend analysis
                    continue

                timestamps.sort()
                frequency = len(timestamps)
                time_span = timestamps[-1] - timestamps[0]

                # Calculate velocity (mentions per hour)
                if time_span.total_seconds() > 0:
                    velocity = frequency / (time_span.total_seconds() / 3600)
                else:
                    velocity = frequency

                # Determine trend type
                trend_type = self._determine_trend_type(timestamps, velocity)

                # Calculate confidence based on frequency and consistency
                confidence = min(frequency / 10.0, 1.0) * 0.7  # Base confidence
                if trend_type in [TrendType.ESCALATING, TrendType.EMERGING]:
                    confidence += 0.2

                # Get related item IDs
                related_items = [
                    item.id for item in items if topic in self._extract_topics(item)
                ]

                trend_analyses[topic] = TrendAnalysis(
                    topic=topic,
                    trend_type=trend_type,
                    frequency=frequency,
                    velocity=velocity,
                    confidence=min(confidence, 1.0),
                    related_items=related_items,
                    time_span=time_span,
                )

            return trend_analyses

        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {}

    def _determine_trend_type(
        self, timestamps: List[datetime], velocity: float
    ) -> TrendType:
        """Determine trend type based on timestamp pattern."""
        try:
            if len(timestamps) < 2:
                return TrendType.STABLE

            # Analyze time intervals
            intervals = []
            for i in range(1, len(timestamps)):
                interval = (
                    timestamps[i] - timestamps[i - 1]
                ).total_seconds() / 3600  # hours
                intervals.append(interval)

            # Calculate trend in intervals (decreasing intervals = escalating)
            if len(intervals) >= 3:
                recent_avg = sum(intervals[-2:]) / 2
                early_avg = sum(intervals[:2]) / 2

                if recent_avg < early_avg * 0.5:  # Recent intervals much shorter
                    return TrendType.ESCALATING
                elif recent_avg > early_avg * 2:  # Recent intervals much longer
                    return TrendType.DECLINING

            # Check if it's a new trend (all recent)
            now = datetime.now(timezone.utc)
            recent_threshold = now - timedelta(hours=6)
            recent_count = sum(1 for ts in timestamps if ts > recent_threshold)

            if recent_count >= len(timestamps) * 0.8:  # 80% are recent
                return TrendType.EMERGING

            # Check for recurring pattern (regular intervals)
            if len(intervals) >= 3:
                avg_interval = sum(intervals) / len(intervals)
                variance = sum((i - avg_interval) ** 2 for i in intervals) / len(
                    intervals
                )
                if variance < avg_interval * 0.3:  # Low variance = regular pattern
                    return TrendType.RECURRING

            return TrendType.STABLE

        except Exception as e:
            logger.error(f"Error determining trend type: {e}")
            return TrendType.STABLE

    def _analyze_item_trends(
        self, item_topics: List[str], trend_analysis: Dict[str, TrendAnalysis]
    ) -> Tuple[Optional[TrendType], float]:
        """Analyze trends for a specific item based on its topics."""
        try:
            if not item_topics:
                return None, 0.0

            # Find the strongest trend among item topics
            max_trend_score = 0.0
            dominant_trend_type = None

            for topic in item_topics:
                if topic in trend_analysis:
                    trend = trend_analysis[topic]

                    # Calculate trend score based on type and confidence
                    type_scores = {
                        TrendType.ESCALATING: 1.0,
                        TrendType.EMERGING: 0.8,
                        TrendType.RECURRING: 0.6,
                        TrendType.STABLE: 0.3,
                        TrendType.DECLINING: 0.2,
                    }

                    trend_score = (
                        type_scores.get(trend.trend_type, 0.3) * trend.confidence
                    )

                    if trend_score > max_trend_score:
                        max_trend_score = trend_score
                        dominant_trend_type = trend.trend_type

            return dominant_trend_type, max_trend_score

        except Exception as e:
            logger.error(f"Error analyzing item trends: {e}")
            return None, 0.0

    async def _extract_action_items(self, item: UnifiedDataItem) -> List[str]:
        """Extract action items from content."""
        try:
            content_text = f"{item.title or ''} {item.content or ''}"
            action_items = []

            # Action item patterns
            patterns = [
                r"(?:todo|task|action):\s*(.+?)(?:\n|$)",
                r"(?:need to|should|must|have to)\s+(.+?)(?:\.|;|$)",
                r"(?:please|can you|could you)\s+(.+?)(?:\.|;|\?|$)",
                r"(?:action item|next step|follow up):\s*(.+?)(?:\n|$)",
                r"(?:assign|delegate|schedule)\s+(.+?)(?:\.|;|$)",
                r"(?:review|approve|complete|finish)\s+(.+?)(?:\.|;|$)",
            ]

            for pattern in patterns:
                matches = re.findall(
                    pattern, content_text, re.IGNORECASE | re.MULTILINE
                )
                for match in matches:
                    cleaned = match.strip()[:100]  # Limit length
                    if cleaned and len(cleaned) > 5:  # Minimum meaningful length
                        action_items.append(cleaned)

            # Deduplicate and limit
            unique_actions = []
            for action in action_items:
                if action not in unique_actions:
                    unique_actions.append(action)

            return unique_actions[:5]  # Return top 5 action items

        except Exception as e:
            logger.error(f"Error extracting action items: {e}")
            return []

    def _detect_risks(self, item: UnifiedDataItem) -> List[str]:
        """Detect risk indicators in content."""
        try:
            content_text = f"{item.title or ''} {item.content or ''}".lower()
            detected_risks = []

            for risk_category, keywords in self.risk_keywords.items():
                if any(keyword in content_text for keyword in keywords):
                    detected_risks.append(risk_category)

            # Additional pattern-based risk detection
            risk_patterns = [
                (r"(?:failed|failure|error|exception)", "technical"),
                (r"(?:delayed|behind|overdue|late)", "schedule"),
                (r"(?:budget|cost|expensive|over budget)", "financial"),
                (r"(?:security|breach|vulnerability|hack)", "security"),
                (r"(?:compliance|violation|audit|regulation)", "compliance"),
            ]

            for pattern, risk_type in risk_patterns:
                if re.search(pattern, content_text) and risk_type not in detected_risks:
                    detected_risks.append(risk_type)

            return detected_risks

        except Exception as e:
            logger.error(f"Error detecting risks: {e}")
            return []

    def _detect_opportunities(self, item: UnifiedDataItem) -> List[str]:
        """Detect opportunity indicators in content."""
        try:
            content_text = f"{item.title or ''} {item.content or ''}".lower()
            detected_opportunities = []

            for opp_category, keywords in self.opportunity_keywords.items():
                if any(keyword in content_text for keyword in keywords):
                    detected_opportunities.append(opp_category)

            # Additional pattern-based opportunity detection
            opp_patterns = [
                (r"(?:success|achievement|win|milestone)", "success"),
                (r"(?:partnership|collaboration|synergy)", "partnership"),
                (r"(?:learning|training|skill|knowledge)", "development"),
                (r"(?:market|customer|user|client)", "market"),
            ]

            for pattern, opp_type in opp_patterns:
                if (
                    re.search(pattern, content_text)
                    and opp_type not in detected_opportunities
                ):
                    detected_opportunities.append(opp_type)

            return detected_opportunities

        except Exception as e:
            logger.error(f"Error detecting opportunities: {e}")
            return []

    def _analyze_sentiment(self, item: UnifiedDataItem) -> float:
        """Analyze sentiment of content (simplified implementation)."""
        try:
            content_text = f"{item.title or ''} {item.content or ''}".lower()

            positive_count = sum(
                1 for word in self.positive_indicators if word in content_text
            )
            negative_count = sum(
                1 for word in self.negative_indicators if word in content_text
            )

            total_sentiment_words = positive_count + negative_count
            if total_sentiment_words == 0:
                return 0.0  # Neutral

            # Calculate sentiment score (-1 to 1)
            sentiment_score = (positive_count - negative_count) / total_sentiment_words

            return sentiment_score

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return 0.0

    def _calculate_confidence(
        self, item: UnifiedDataItem, importance_score: float, urgency_score: float
    ) -> float:
        """Calculate confidence in the intelligence analysis."""
        try:
            confidence = 0.5  # Base confidence

            # Content quality affects confidence
            content_text = f"{item.title or ''} {item.content or ''}"
            if len(content_text) > 50:
                confidence += 0.1
            if len(content_text) > 200:
                confidence += 0.1

            # Clear indicators increase confidence
            if importance_score > 0.8 or urgency_score > 0.8:
                confidence += 0.2

            # Metadata completeness
            if item.author:
                confidence += 0.05
            if item.created_at:
                confidence += 0.05
            if item.categories:
                confidence += 0.05
            if item.tags:
                confidence += 0.05

            return min(confidence, 1.0)

        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5

    def _generate_reasoning(
        self,
        item: UnifiedDataItem,
        importance_score: float,
        urgency_level: UrgencyLevel,
        trend_type: Optional[TrendType],
        action_count: int,
        risk_count: int,
        opportunity_count: int,
    ) -> str:
        """Generate human-readable reasoning for the intelligence analysis."""
        try:
            reasons = []

            # Importance reasoning
            if importance_score > 0.8:
                reasons.append("High importance due to critical keywords and context")
            elif importance_score > 0.6:
                reasons.append("Medium-high importance based on content analysis")
            elif importance_score < 0.3:
                reasons.append("Low importance - routine or informational content")

            # Urgency reasoning
            if urgency_level != UrgencyLevel.NORMAL:
                reasons.append(
                    f"Urgency level: {urgency_level.value} - time-sensitive content detected"
                )

            # Trend reasoning
            if trend_type:
                reasons.append(f"Part of {trend_type.value} trend - requires attention")

            # Action items
            if action_count > 0:
                reasons.append(f"{action_count} action item(s) identified")

            # Risks and opportunities
            if risk_count > 0:
                reasons.append(f"{risk_count} risk indicator(s) detected")
            if opportunity_count > 0:
                reasons.append(f"{opportunity_count} opportunity indicator(s) found")

            # Content type specific reasoning
            if item.content_type == ContentType.ISSUE:
                reasons.append("Software issue - may require technical attention")
            elif item.content_type == ContentType.EMAIL:
                reasons.append("Email communication - check for responses needed")

            return "; ".join(reasons) if reasons else "Standard content analysis"

        except Exception as e:
            logger.error(f"Error generating reasoning: {e}")
            return "Analysis completed with basic heuristics"

    async def _normalize_scores(
        self, intelligence_results: List[ContentIntelligence]
    ) -> List[ContentIntelligence]:
        """Normalize scores across all items for relative ranking."""
        try:
            if not intelligence_results:
                return intelligence_results

            # Get score distributions
            importance_scores = [r.importance_score for r in intelligence_results]
            urgency_scores = [r.urgency_score for r in intelligence_results]
            trend_scores = [r.trend_score for r in intelligence_results]

            # Calculate percentile-based normalization
            importance_scores.sort()
            urgency_scores.sort()
            trend_scores.sort()

            def percentile_normalize(value: float, sorted_values: List[float]) -> float:
                if not sorted_values:
                    return value

                # Find position in sorted list
                position = 0
                for i, v in enumerate(sorted_values):
                    if value <= v:
                        position = i
                        break
                else:
                    position = len(sorted_values) - 1

                # Convert to percentile (0-1)
                return position / max(len(sorted_values) - 1, 1)

            # Apply normalization
            for result in intelligence_results:
                # Keep original scores but add normalized versions
                result.importance_score = (
                    result.importance_score * 0.7
                    + percentile_normalize(result.importance_score, importance_scores)
                    * 0.3
                )
                result.urgency_score = (
                    result.urgency_score * 0.8
                    + percentile_normalize(result.urgency_score, urgency_scores) * 0.2
                )
                result.trend_score = (
                    result.trend_score * 0.9
                    + percentile_normalize(result.trend_score, trend_scores) * 0.1
                )

            return intelligence_results

        except Exception as e:
            logger.error(f"Error normalizing scores: {e}")
            return intelligence_results

# Global service instance
content_intelligence_service = ContentIntelligenceService()
