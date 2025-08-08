"""Brief Generation Engine for SingleBrief.

This module provides automated brief generation with template-based rendering,
content aggregation, intelligent prioritization, and multi-format output.
"""

import hashlib
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import jinja2
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.integration import DataSource, Integration
from app.models.user import Organization, User
from app.services.data_normalization import (ContentType, SourceType,
                                             UnifiedDataItem,
                                             data_normalization_service)

logger = logging.getLogger(__name__)

class BriefFormat(Enum):
    """Enumeration of brief output formats."""

    HTML = "html"
    TEXT = "text"
    PDF = "pdf"
    EMAIL = "email"
    SLACK = "slack"

class BriefSection(Enum):
    """Enumeration of brief sections."""

    EXECUTIVE_SUMMARY = "executive_summary"
    URGENT_ITEMS = "urgent_items"
    ACTION_ITEMS = "action_items"
    RECENT_ACTIVITY = "recent_activity"
    TEAM_UPDATES = "team_updates"
    PROJECT_STATUS = "project_status"
    DEVELOPMENT_METRICS = "development_metrics"
    DOCUMENT_UPDATES = "document_updates"
    CALENDAR_HIGHLIGHTS = "calendar_highlights"
    TRENDING_TOPICS = "trending_topics"

@dataclass

class BriefContent:
    """Container for brief content data."""

    section: BriefSection
    title: str
    content: str
    items: List[Dict[str, Any]]
    priority_score: float
    confidence_score: float
    source_attribution: List[str]
    last_updated: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template rendering."""
        return {
            "section": self.section.value,
            "title": self.title,
            "content": self.content,
            "items": self.items,
            "priority_score": self.priority_score,
            "confidence_score": self.confidence_score,
            "source_attribution": self.source_attribution,
            "last_updated": (
                self.last_updated.isoformat() if self.last_updated else None
            ),
        }

@dataclass

class BriefConfig:
    """Configuration for brief generation."""

    user_id: str
    organization_id: str
    brief_type: str = "daily"
    format: BriefFormat = BriefFormat.HTML
    sections: List[BriefSection] = None
    timezone: str = "UTC"
    max_items_per_section: int = 10
    include_sources: List[SourceType] = None
    exclude_sources: List[SourceType] = None
    priority_threshold: float = 0.5
    time_range_hours: int = 24

    def __post_init__(self):
        """Initialize default values."""
        if self.sections is None:
            self.sections = [
                BriefSection.EXECUTIVE_SUMMARY,
                BriefSection.URGENT_ITEMS,
                BriefSection.ACTION_ITEMS,
                BriefSection.RECENT_ACTIVITY,
                BriefSection.TEAM_UPDATES,
            ]
        if self.include_sources is None:
            self.include_sources = []

@dataclass

class GeneratedBrief:
    """Container for a generated brief."""

    id: str
    user_id: str
    organization_id: str
    config: BriefConfig
    sections: List[BriefContent]
    generated_at: datetime
    format: BriefFormat
    content_hash: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage and API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "config": asdict(self.config),
            "sections": [section.to_dict() for section in self.sections],
            "generated_at": self.generated_at.isoformat(),
            "format": self.format.value,
            "content_hash": self.content_hash,
            "metadata": self.generation_metadata,
        }

class BriefGenerationService:
    """Service for automated brief generation and content intelligence."""

    def __init__(self):
        self.session: Optional[AsyncSession] = None

        # Template configuration
        self.template_dir = Path(__file__).parent.parent / "templates" / "briefs"
        self.template_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Content intelligence thresholds
        self.urgency_keywords = [
            "urgent",
            "asap",
            "critical",
            "emergency",
            "deadline",
            "overdue",
            "immediate",
            "priority",
            "escalation",
            "alert",
            "warning",
        ]

        self.action_keywords = [
            "todo",
            "task",
            "action",
            "follow up",
            "next steps",
            "deliverable",
            "milestone",
            "complete",
            "finish",
            "review",
            "approve",
        ]

        # Brief generation cache
        self.brief_cache = {}
        self.cache_ttl = 300  # 5 minutes

    async def get_session(self) -> AsyncSession:
        """Get database session."""
        if self.session is None:
            self.session = await get_db_session().__anext__()
        return self.session

    async def generate_brief(
        self, config: BriefConfig, use_cache: bool = True
    ) -> GeneratedBrief:
        """Generate a comprehensive brief based on configuration."""
        try:
            # Check cache first
            cache_key = self._generate_cache_key(config)
            if use_cache and cache_key in self.brief_cache:
                cached_brief, cached_time = self.brief_cache[cache_key]
                if (datetime.now(timezone.utc) - cached_time).seconds < self.cache_ttl:
                    logger.info(f"Returning cached brief for user {config.user_id}")
                    return cached_brief

            logger.info(f"Generating new brief for user {config.user_id}")

            # Aggregate content from all sources
            aggregated_content = await self._aggregate_content(config)

            # Apply content intelligence and prioritization
            intelligent_content = await self._apply_content_intelligence(
                aggregated_content, config
            )

            # Generate sections
            sections = await self._generate_sections(intelligent_content, config)

            # Create brief
            brief_id = (
                f"brief_{config.user_id}_{int(datetime.now(timezone.utc).timestamp())}"
            )
            content_hash = self._calculate_content_hash(sections)

            generated_brief = GeneratedBrief(
                id=brief_id,
                user_id=config.user_id,
                organization_id=config.organization_id,
                config=config,
                sections=sections,
                generated_at=datetime.now(timezone.utc),
                format=config.format,
                content_hash=content_hash,
                metadata={
                    "total_sections": len(sections),
                    "total_items": sum(len(section.items) for section in sections),
                    "sources_used": list(
                        set(
                            source
                            for section in sections
                            for source in section.source_attribution
                        )
                    ),
                    "generation_time_ms": 0,  # TODO: Add timing
                },
            )

            # Cache the brief
            self.brief_cache[cache_key] = (generated_brief, datetime.now(timezone.utc))

            # Store in database (TODO: Create BriefHistory model)
            await self._store_brief_history(generated_brief)

            return generated_brief

        except Exception as e:
            logger.error(f"Error generating brief: {e}")
            raise

    async def _aggregate_content(self, config: BriefConfig) -> List[UnifiedDataItem]:
        """Aggregate content from all integrated sources."""
        try:
            # Calculate time range
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=config.time_range_hours)

            # Build search filters
            source_types = config.include_sources if config.include_sources else None
            if config.exclude_sources:
                if source_types:
                    source_types = [
                        st for st in source_types if st not in config.exclude_sources
                    ]
                else:
                    source_types = [
                        st for st in SourceType if st not in config.exclude_sources
                    ]

            # Search for relevant content
            search_results = await data_normalization_service.search_unified_data(
                query="",  # Get all content
                content_types=None,
                source_types=source_types,
                date_range=(start_time, end_time),
                limit=1000,  # Large limit for comprehensive aggregation
            )

            # Convert search results to UnifiedDataItem objects
            aggregated_items = []
            for item_data in search_results.get("items", []):
                # Reconstruct UnifiedDataItem from search result
                try:
                    # Parse source and content types
                    source_type = SourceType(item_data.get("source_type", "unknown"))
                    content_type = ContentType(item_data.get("content_type", "unknown"))

                    # Parse timestamps
                    created_at = None
                    updated_at = None
                    if item_data.get("created_at"):
                        created_at = datetime.fromisoformat(
                            item_data["created_at"].replace("Z", "+00:00")
                        )
                    if item_data.get("updated_at"):
                        updated_at = datetime.fromisoformat(
                            item_data["updated_at"].replace("Z", "+00:00")
                        )

                    unified_item = UnifiedDataItem(
                        id=item_data.get("id", ""),
                        source_type=source_type,
                        source_id=item_data.get("source_id", ""),
                        content_type=content_type,
                        title=item_data.get("title"),
                        content=item_data.get("content"),
                        author=item_data.get("author"),
                        author_email=item_data.get("author_email"),
                        participants=item_data.get("participants", []),
                        tags=item_data.get("tags", []),
                        categories=item_data.get("categories", []),
                        created_at=created_at,
                        updated_at=updated_at,
                        source_metadata=item_data.get("source_metadata", {}),
                        relevance_score=item_data.get("relevance_score", 0.0),
                        freshness_score=item_data.get("freshness_score", 0.0),
                        quality_score=item_data.get("quality_score", 0.0),
                    )

                    aggregated_items.append(unified_item)

                except Exception as e:
                    logger.warning(f"Error parsing search result item: {e}")
                    continue

            logger.info(f"Aggregated {len(aggregated_items)} content items for brief")
            return aggregated_items

        except Exception as e:
            logger.error(f"Error aggregating content: {e}")
            return []

    async def _apply_content_intelligence(
        self, content: List[UnifiedDataItem], config: BriefConfig
    ) -> List[UnifiedDataItem]:
        """Apply content intelligence and prioritization."""
        try:
            enhanced_content = []

            for item in content:
                # Calculate enhanced scores
                item.relevance_score = await self._calculate_importance_score(
                    item, config
                )
                urgency_score = await self._detect_urgency(item)
                trend_score = await self._analyze_trends(item, content)

                # Add intelligence metadata
                item.source_metadata["intelligence"] = {
                    "urgency_score": urgency_score,
                    "trend_score": trend_score,
                    "action_items": await self._extract_action_items(item),
                    "risk_indicators": await self._detect_risks(item),
                    "opportunity_indicators": await self._detect_opportunities(item),
                }

                # Filter by priority threshold
                combined_score = (
                    item.relevance_score * 0.4
                    + urgency_score * 0.3
                    + trend_score * 0.2
                    + item.freshness_score * 0.1
                )

                if combined_score >= config.priority_threshold:
                    enhanced_content.append(item)

            # Sort by combined priority score
            enhanced_content.sort(
                key=lambda x: x.source_metadata.get("intelligence", {}).get(
                    "combined_score", 0
                ),
                reverse=True,
            )

            logger.info(
                f"Enhanced {len(enhanced_content)} items after intelligence filtering"
            )
            return enhanced_content

        except Exception as e:
            logger.error(f"Error applying content intelligence: {e}")
            return content

    async def _calculate_importance_score(
        self, item: UnifiedDataItem, config: BriefConfig
    ) -> float:
        """Calculate importance score based on multiple factors."""
        try:
            score = 0.0

            # Content type weighting
            content_weights = {
                ContentType.EMAIL: 0.8,
                ContentType.MESSAGE: 0.7,
                ContentType.ISSUE: 0.9,
                ContentType.PULL_REQUEST: 0.8,
                ContentType.DOCUMENT: 0.6,
                ContentType.CALENDAR_EVENT: 0.7,
            }
            score += content_weights.get(item.content_type, 0.5)

            # Author importance (placeholder - could integrate with org chart)
            if item.author:
                if any(
                    keyword in (item.author or "").lower()
                    for keyword in ["ceo", "manager", "director", "lead"]
                ):
                    score += 0.3
                elif any(
                    keyword in (item.author or "").lower()
                    for keyword in ["senior", "principal"]
                ):
                    score += 0.2

            # Participant count (more people = potentially more important)
            participant_bonus = min(len(item.participants or []) * 0.05, 0.3)
            score += participant_bonus

            # Content length and quality
            content_text = f"{item.title or ''} {item.content or ''}"
            if len(content_text) > 100:
                score += 0.1
            if len(content_text) > 500:
                score += 0.1

            # Tag-based importance
            important_tags = [
                "urgent",
                "critical",
                "important",
                "priority",
                "milestone",
            ]
            if any(tag.lower() in important_tags for tag in (item.tags or [])):
                score += 0.4

            # Category-based importance
            important_categories = [
                "meeting",
                "action_item",
                "technical_issue",
                "project_management",
            ]
            if any(cat in important_categories for cat in (item.categories or [])):
                score += 0.2

            # Freshness factor
            score += item.freshness_score * 0.2

            # Quality factor
            score += item.quality_score * 0.1

            return min(score, 1.0)

        except Exception as e:
            logger.error(f"Error calculating importance score: {e}")
            return 0.5

    async def _detect_urgency(self, item: UnifiedDataItem) -> float:
        """Detect urgency indicators in content."""
        try:
            urgency_score = 0.0
            content_text = f"{item.title or ''} {item.content or ''}".lower()

            # Keyword-based urgency
            urgency_matches = sum(
                1 for keyword in self.urgency_keywords if keyword in content_text
            )
            urgency_score += min(urgency_matches * 0.2, 0.6)

            # Time-based urgency (deadlines, dates)
            import re

            # Look for deadline patterns
            deadline_patterns = [
                r"deadline.*?(today|tomorrow|this week)",
                r"due.*?(today|tomorrow|asap)",
                r"expires.*?(today|tomorrow|soon)",
                r"urgent.*?by.*?(today|tomorrow)",
            ]

            for pattern in deadline_patterns:
                if re.search(pattern, content_text):
                    urgency_score += 0.3
                    break

            # Recent creation with urgent keywords
            if item.created_at and item.created_at > datetime.now(
                timezone.utc
            ) - timedelta(hours=2):
                if urgency_matches > 0:
                    urgency_score += 0.2

            # Category-based urgency
            urgent_categories = ["technical_issue", "action_item"]
            if any(cat in urgent_categories for cat in (item.categories or [])):
                urgency_score += 0.1

            return min(urgency_score, 1.0)

        except Exception as e:
            logger.error(f"Error detecting urgency: {e}")
            return 0.0

    async def _analyze_trends(
        self, item: UnifiedDataItem, all_content: List[UnifiedDataItem]
    ) -> float:
        """Analyze trends and patterns in content."""
        try:
            trend_score = 0.0

            # Topic frequency analysis
            item_keywords = self._extract_keywords(item)

            # Count occurrences of similar keywords in other content
            similar_content_count = 0
            for other_item in all_content:
                if other_item.id != item.id:
                    other_keywords = self._extract_keywords(other_item)
                    if len(set(item_keywords) & set(other_keywords)) >= 2:
                        similar_content_count += 1

            # Trending topic bonus
            if similar_content_count >= 3:
                trend_score += 0.4
            elif similar_content_count >= 2:
                trend_score += 0.2

            # Escalation pattern (multiple mentions of same issue)
            if item.content_type in [ContentType.ISSUE, ContentType.MESSAGE]:
                content_lower = (item.content or "").lower()
                if any(
                    word in content_lower
                    for word in ["still", "again", "repeatedly", "continues"]
                ):
                    trend_score += 0.3

            # Cross-source mentions (same topic across different sources)
            cross_source_count = len(
                set(
                    other_item.source_type
                    for other_item in all_content
                    if other_item.id != item.id
                    and len(
                        set(self._extract_keywords(other_item)) & set(item_keywords)
                    )
                    >= 1
                )
            )

            if cross_source_count >= 2:
                trend_score += 0.2

            return min(trend_score, 1.0)

        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return 0.0

    def _extract_keywords(self, item: UnifiedDataItem) -> List[str]:
        """Extract keywords from content for trend analysis."""
        import re

        content_text = f"{item.title or ''} {item.content or ''}"

        # Simple keyword extraction (could be enhanced with NLP)
        words = re.findall(r"\b[a-zA-Z]{4,}\b", content_text.lower())

        # Filter out common words
        stop_words = {
            "this",
            "that",
            "with",
            "have",
            "will",
            "from",
            "they",
            "been",
            "have",
            "were",
            "said",
            "each",
            "which",
            "their",
            "time",
            "about",
        }

        keywords = [word for word in words if word not in stop_words]
        return keywords[:10]  # Return top 10 keywords

    async def _extract_action_items(self, item: UnifiedDataItem) -> List[str]:
        """Extract action items from content."""
        try:
            action_items = []
            content_text = f"{item.title or ''} {item.content or ''}"

            # Look for action item patterns
            import re

            action_patterns = [
                r"(?:todo|task|action):\s*(.+?)(?:\n|$)",
                r"(?:please|need to|should|must)\s+(.+?)(?:\.|$)",
                r"(?:follow up|next steps?):\s*(.+?)(?:\n|$)",
                r"(?:assign|delegate|schedule)\s+(.+?)(?:\.|$)",
            ]

            for pattern in action_patterns:
                matches = re.findall(
                    pattern, content_text, re.IGNORECASE | re.MULTILINE
                )
                action_items.extend(matches[:3])  # Limit to 3 per pattern

            # Clean and deduplicate
            cleaned_items = []
            for item_text in action_items:
                cleaned = item_text.strip()[:100]  # Limit length
                if cleaned and cleaned not in cleaned_items:
                    cleaned_items.append(cleaned)

            return cleaned_items[:5]  # Return top 5 action items

        except Exception as e:
            logger.error(f"Error extracting action items: {e}")
            return []

    async def _detect_risks(self, item: UnifiedDataItem) -> List[str]:
        """Detect risk indicators in content."""
        try:
            risks = []
            content_text = f"{item.title or ''} {item.content or ''}".lower()

            # Risk keywords and patterns
            risk_indicators = {
                "technical": [
                    "outage",
                    "down",
                    "error",
                    "failure",
                    "bug",
                    "security breach",
                ],
                "timeline": ["delay", "behind schedule", "overdue", "missed deadline"],
                "resource": ["shortage", "unavailable", "blocked", "capacity"],
                "quality": ["defect", "issue", "problem", "concern", "escalation"],
            }

            for risk_type, keywords in risk_indicators.items():
                if any(keyword in content_text for keyword in keywords):
                    risks.append(risk_type)

            return risks

        except Exception as e:
            logger.error(f"Error detecting risks: {e}")
            return []

    async def _detect_opportunities(self, item: UnifiedDataItem) -> List[str]:
        """Detect opportunity indicators in content."""
        try:
            opportunities = []
            content_text = f"{item.title or ''} {item.content or ''}".lower()

            # Opportunity keywords and patterns
            opportunity_indicators = {
                "optimization": ["improve", "optimize", "enhance", "streamline"],
                "growth": ["expand", "scale", "increase", "opportunity"],
                "efficiency": ["automate", "reduce", "faster", "simplify"],
                "innovation": ["new", "innovative", "creative", "breakthrough"],
            }

            for opp_type, keywords in opportunity_indicators.items():
                if any(keyword in content_text for keyword in keywords):
                    opportunities.append(opp_type)

            return opportunities

        except Exception as e:
            logger.error(f"Error detecting opportunities: {e}")
            return []

    async def _generate_sections(
        self, content: List[UnifiedDataItem], config: BriefConfig
    ) -> List[BriefContent]:
        """Generate brief sections based on intelligent content."""
        try:
            sections = []

            for section_type in config.sections:
                section_content = await self._generate_section_content(
                    section_type, content, config
                )
                if section_content:
                    sections.append(section_content)

            return sections

        except Exception as e:
            logger.error(f"Error generating sections: {e}")
            return []

    async def _generate_section_content(
        self,
        section_type: BriefSection,
        content: List[UnifiedDataItem],
        config: BriefConfig,
    ) -> Optional[BriefContent]:
        """Generate content for a specific brief section."""
        try:
            if section_type == BriefSection.EXECUTIVE_SUMMARY:
                return await self._generate_executive_summary(content, config)
            elif section_type == BriefSection.URGENT_ITEMS:
                return await self._generate_urgent_items(content, config)
            elif section_type == BriefSection.ACTION_ITEMS:
                return await self._generate_action_items(content, config)
            elif section_type == BriefSection.RECENT_ACTIVITY:
                return await self._generate_recent_activity(content, config)
            elif section_type == BriefSection.TEAM_UPDATES:
                return await self._generate_team_updates(content, config)
            elif section_type == BriefSection.PROJECT_STATUS:
                return await self._generate_project_status(content, config)
            elif section_type == BriefSection.DEVELOPMENT_METRICS:
                return await self._generate_development_metrics(content, config)
            elif section_type == BriefSection.DOCUMENT_UPDATES:
                return await self._generate_document_updates(content, config)
            elif section_type == BriefSection.CALENDAR_HIGHLIGHTS:
                return await self._generate_calendar_highlights(content, config)
            elif section_type == BriefSection.TRENDING_TOPICS:
                return await self._generate_trending_topics(content, config)
            else:
                logger.warning(f"Unknown section type: {section_type}")
                return None

        except Exception as e:
            logger.error(f"Error generating section {section_type}: {e}")
            return None

    async def _generate_executive_summary(
        self, content: List[UnifiedDataItem], config: BriefConfig
    ) -> BriefContent:
        """Generate executive summary section."""
        # Get top priority items
        top_items = sorted(content, key=lambda x: x.relevance_score, reverse=True)[:5]

        # Analyze key themes
        urgent_count = sum(
            1
            for item in content
            if item.source_metadata.get("intelligence", {}).get("urgency_score", 0)
            > 0.5
        )
        action_count = sum(
            len(item.source_metadata.get("intelligence", {}).get("action_items", []))
            for item in content
        )

        summary_text = f"Key highlights from the last {config.time_range_hours} hours: "
        summary_text += f"{len(content)} total items reviewed, "
        summary_text += f"{urgent_count} urgent items requiring attention, "
        summary_text += f"{action_count} action items identified."

        items = [
            {
                "title": item.title
                or f"{item.content_type.value.title()} from {item.source_type.value}",
                "content": (
                    (item.content or "")[:200] + "..."
                    if len(item.content or "") > 200
                    else item.content
                ),
                "score": item.relevance_score,
                "source": item.source_type.value,
                "urgency": item.source_metadata.get("intelligence", {}).get(
                    "urgency_score", 0
                ),
            }
            for item in top_items
        ]

        return BriefContent(
            section=BriefSection.EXECUTIVE_SUMMARY,
            title="Executive Summary",
            content=summary_text,
            items=items,
            priority_score=1.0,
            confidence_score=0.9,
            source_attribution=list(set(item.source_type.value for item in top_items)),
            last_updated=datetime.now(timezone.utc),
        )

    async def _generate_urgent_items(
        self, content: List[UnifiedDataItem], config: BriefConfig
    ) -> Optional[BriefContent]:
        """Generate urgent items section."""
        urgent_items = [
            item
            for item in content
            if item.source_metadata.get("intelligence", {}).get("urgency_score", 0)
            > 0.5
        ]

        if not urgent_items:
            return None

        # Sort by urgency score
        urgent_items.sort(
            key=lambda x: x.source_metadata.get("intelligence", {}).get(
                "urgency_score", 0
            ),
            reverse=True,
        )

        items = [
            {
                "title": item.title or f"Urgent: {item.content_type.value.title()}",
                "content": (
                    (item.content or "")[:150] + "..."
                    if len(item.content or "") > 150
                    else item.content
                ),
                "urgency_score": item.source_metadata.get("intelligence", {}).get(
                    "urgency_score", 0
                ),
                "source": item.source_type.value,
                "author": item.author,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in urgent_items[: config.max_items_per_section]
        ]

        return BriefContent(
            section=BriefSection.URGENT_ITEMS,
            title="Urgent Items Requiring Attention",
            content=f"{len(urgent_items)} urgent items identified",
            items=items,
            priority_score=0.95,
            confidence_score=0.85,
            source_attribution=list(
                set(item.source_type.value for item in urgent_items)
            ),
            last_updated=datetime.now(timezone.utc),
        )

    async def _generate_action_items(
        self, content: List[UnifiedDataItem], config: BriefConfig
    ) -> Optional[BriefContent]:
        """Generate action items section."""
        all_action_items = []

        for item in content:
            actions = item.source_metadata.get("intelligence", {}).get(
                "action_items", []
            )
            for action in actions:
                all_action_items.append(
                    {
                        "action": action,
                        "source_title": item.title
                        or f"{item.content_type.value.title()}",
                        "source_type": item.source_type.value,
                        "author": item.author,
                        "priority": item.relevance_score,
                        "created_at": (
                            item.created_at.isoformat() if item.created_at else None
                        ),
                    }
                )

        if not all_action_items:
            return None

        # Sort by priority
        all_action_items.sort(key=lambda x: x["priority"], reverse=True)

        return BriefContent(
            section=BriefSection.ACTION_ITEMS,
            title="Action Items & Next Steps",
            content=f"{len(all_action_items)} action items extracted from communications",
            items=all_action_items[: config.max_items_per_section],
            priority_score=0.8,
            confidence_score=0.7,
            source_attribution=list(
                set(item["source_type"] for item in all_action_items)
            ),
            last_updated=datetime.now(timezone.utc),
        )

    async def _generate_recent_activity(
        self, content: List[UnifiedDataItem], config: BriefConfig
    ) -> BriefContent:
        """Generate recent activity section."""
        # Sort by recency
        recent_items = sorted(
            content,
            key=lambda x: x.updated_at
            or x.created_at
            or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )

        items = [
            {
                "title": item.title or f"{item.content_type.value.title()} Update",
                "content": (
                    (item.content or "")[:100] + "..."
                    if len(item.content or "") > 100
                    else item.content
                ),
                "source": item.source_type.value,
                "author": item.author,
                "updated_at": (
                    (item.updated_at or item.created_at).isoformat()
                    if (item.updated_at or item.created_at)
                    else None
                ),
                "participants": (
                    item.participants[:3] if item.participants else []
                ),  # Limit participants
            }
            for item in recent_items[: config.max_items_per_section]
        ]

        return BriefContent(
            section=BriefSection.RECENT_ACTIVITY,
            title="Recent Activity",
            content=f"Latest updates across all integrated sources",
            items=items,
            priority_score=0.6,
            confidence_score=0.8,
            source_attribution=list(
                set(
                    item.source_type.value
                    for item in recent_items[: config.max_items_per_section]
                )
            ),
            last_updated=datetime.now(timezone.utc),
        )

    async def _generate_team_updates(
        self, content: List[UnifiedDataItem], config: BriefConfig
    ) -> Optional[BriefContent]:
        """Generate team updates section."""
        # Filter for team-related content
        team_content = [
            item
            for item in content
            if len(item.participants or []) > 1
            or any(
                cat in ["meeting", "project_management"]
                for cat in (item.categories or [])
            )
        ]

        if not team_content:
            return None

        items = [
            {
                "title": item.title
                or f"Team Update: {item.content_type.value.title()}",
                "content": (
                    (item.content or "")[:150] + "..."
                    if len(item.content or "") > 150
                    else item.content
                ),
                "participants": item.participants[:5] if item.participants else [],
                "source": item.source_type.value,
                "categories": item.categories or [],
            }
            for item in team_content[: config.max_items_per_section]
        ]

        return BriefContent(
            section=BriefSection.TEAM_UPDATES,
            title="Team Updates & Collaboration",
            content=f"Team activities and collaborative updates",
            items=items,
            priority_score=0.7,
            confidence_score=0.75,
            source_attribution=list(
                set(item.source_type.value for item in team_content)
            ),
            last_updated=datetime.now(timezone.utc),
        )

    # Placeholder implementations for other section generators
    async def _generate_project_status(
        self, content: List[UnifiedDataItem], config: BriefConfig
    ) -> Optional[BriefContent]:
        """Generate project status section."""
        # Filter for project-related content (GitHub issues, Jira tickets, etc.)
        project_content = [
            item
            for item in content
            if item.content_type in [ContentType.ISSUE, ContentType.PULL_REQUEST]
        ]
        if not project_content:
            return None

        items = [
            {"title": item.title, "status": "placeholder"}
            for item in project_content[:5]
        ]
        return BriefContent(
            section=BriefSection.PROJECT_STATUS,
            title="Project Status Updates",
            content="Development and project updates",
            items=items,
            priority_score=0.7,
            confidence_score=0.6,
            source_attribution=["github", "jira"],
            last_updated=datetime.now(timezone.utc),
        )

    async def _generate_development_metrics(
        self, content: List[UnifiedDataItem], config: BriefConfig
    ) -> Optional[BriefContent]:
        """Generate development metrics section."""
        # Placeholder implementation
        return None

    async def _generate_document_updates(
        self, content: List[UnifiedDataItem], config: BriefConfig
    ) -> Optional[BriefContent]:
        """Generate document updates section."""
        doc_content = [
            item for item in content if item.content_type == ContentType.DOCUMENT
        ]
        if not doc_content:
            return None

        items = [
            {"title": item.title, "updated": "placeholder"} for item in doc_content[:5]
        ]
        return BriefContent(
            section=BriefSection.DOCUMENT_UPDATES,
            title="Document Updates",
            content="Recent document changes",
            items=items,
            priority_score=0.5,
            confidence_score=0.7,
            source_attribution=["gdrive", "onedrive"],
            last_updated=datetime.now(timezone.utc),
        )

    async def _generate_calendar_highlights(
        self, content: List[UnifiedDataItem], config: BriefConfig
    ) -> Optional[BriefContent]:
        """Generate calendar highlights section."""
        calendar_content = [
            item for item in content if item.content_type == ContentType.CALENDAR_EVENT
        ]
        if not calendar_content:
            return None

        items = [
            {"title": item.title, "time": "placeholder"}
            for item in calendar_content[:5]
        ]
        return BriefContent(
            section=BriefSection.CALENDAR_HIGHLIGHTS,
            title="Calendar Highlights",
            content="Upcoming calendar events",
            items=items,
            priority_score=0.6,
            confidence_score=0.8,
            source_attribution=["gmail", "outlook"],
            last_updated=datetime.now(timezone.utc),
        )

    async def _generate_trending_topics(
        self, content: List[UnifiedDataItem], config: BriefConfig
    ) -> Optional[BriefContent]:
        """Generate trending topics section."""
        # Analyze keywords and trends across content
        keyword_counts = {}
        for item in content:
            keywords = self._extract_keywords(item)
            for keyword in keywords:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

        # Get top trending keywords
        trending = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        if not trending:
            return None

        items = [{"topic": topic, "mentions": count} for topic, count in trending]

        return BriefContent(
            section=BriefSection.TRENDING_TOPICS,
            title="Trending Topics",
            content="Most discussed topics across all sources",
            items=items,
            priority_score=0.4,
            confidence_score=0.6,
            source_attribution=list(set(item.source_type.value for item in content)),
            last_updated=datetime.now(timezone.utc),
        )

    def _generate_cache_key(self, config: BriefConfig) -> str:
        """Generate cache key for brief configuration."""
        key_data = f"{config.user_id}_{config.organization_id}_{config.brief_type}_{config.time_range_hours}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _calculate_content_hash(self, sections: List[BriefContent]) -> str:
        """Calculate hash of brief content for versioning."""
        content_str = "".join(
            f"{section.section.value}_{section.title}_{len(section.items)}"
            for section in sections
        )
        return hashlib.sha256(content_str.encode()).hexdigest()

    async def _store_brief_history(self, brief: GeneratedBrief):
        """Store brief in history for tracking and analytics."""
        # TODO: Implement brief history storage
        # This would store the generated brief in a database table
        # for analytics, versioning, and user access to past briefs
        logger.info(f"Storing brief {brief.id} in history (placeholder)")

    async def render_brief_template(
        self, brief: GeneratedBrief, format: BriefFormat = BriefFormat.HTML
    ) -> str:
        """Render brief using Jinja2 templates."""
        try:
            # Select template based on format
            template_name = f"brief_{format.value}.j2"

            # Get template
            template = self.template_env.get_template(template_name)

            # Prepare template context
            context = {
                "brief": brief.to_dict(),
                "generated_at": brief.generated_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "user_id": brief.user_id,
                "organization_id": brief.organization_id,
                "sections": [section.to_dict() for section in brief.sections],
                "metadata": brief.generation_metadata,
            }

            # Render template
            rendered_content = template.render(**context)

            return rendered_content

        except Exception as e:
            logger.error(f"Error rendering brief template: {e}")
            # Return fallback content
            return f"Brief generated at {brief.generated_at} with {len(brief.sections)} sections"

# Global service instance
brief_generation_service = BriefGenerationService()
