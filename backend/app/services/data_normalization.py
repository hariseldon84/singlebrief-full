"""Data Normalization and Search Layer for SingleBrief.

This module provides unified data schema, full-text search, metadata management,
content classification, and deduplication across all integrated sources.
"""

from typing import Any, Dict, List, Optional, Tuple

import hashlib
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum

import aiohttp
from sqlalchemy import and_, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.integration import DataSource, Integration

logger = logging.getLogger(__name__)

class ContentType(Enum):
    """Enumeration of content types."""

    MESSAGE = "message"
    EMAIL = "email"
    DOCUMENT = "document"
    CALENDAR_EVENT = "calendar_event"
    ISSUE = "issue"
    PULL_REQUEST = "pull_request"
    REPOSITORY = "repository"
    PROJECT = "project"
    CONTACT = "contact"
    THREAD = "thread"
    UNKNOWN = "unknown"

class SourceType(Enum):
    """Enumeration of source systems."""

    SLACK = "slack"
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    GDRIVE = "gdrive"
    ONEDRIVE = "onedrive"
    GITHUB = "github"
    JIRA = "jira"
    UNKNOWN = "unknown"

@dataclass

class UnifiedDataItem:
    """Unified data schema for all external sources."""

    # Core identification
    id: str
    source_type: SourceType
    source_id: str
    content_type: ContentType

    # Content
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None

    # Metadata
    author: Optional[str] = None
    author_email: Optional[str] = None
    participants: List[str] = None
    tags: List[str] = None
    categories: List[str] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    indexed_at: Optional[datetime] = None

    # Source-specific metadata
    source_metadata: Dict[str, Any] = None

    # Search and ranking
    relevance_score: float = 0.0
    freshness_score: float = 0.0
    quality_score: float = 0.0

    # Relationships
    parent_id: Optional[str] = None
    thread_id: Optional[str] = None
    related_ids: List[str] = None

    # Processing metadata
    duplicate_of: Optional[str] = None
    duplicate_confidence: float = 0.0
    classification_confidence: float = 0.0

    def __post_init__(self):
        """Initialize default values."""
        if self.participants is None:
            self.participants = []
        if self.tags is None:
            self.tags = []
        if self.categories is None:
            self.categories = []
        if self.source_metadata is None:
            self.source_metadata = {}
        if self.related_ids is None:
            self.related_ids = []
        if self.indexed_at is None:
            self.indexed_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)

        # Convert enums to strings
        result["source_type"] = self.source_type.value
        result["content_type"] = self.content_type.value

        # Convert datetime objects to ISO strings
        for field in ["created_at", "updated_at", "indexed_at"]:
            if result[field]:
                result[field] = result[field].isoformat()

        return result

    def content_hash(self) -> str:
        """Generate content hash for deduplication."""
        content_str = f"{self.title or ''}{self.content or ''}{self.author or ''}"
        return hashlib.sha256(content_str.encode()).hexdigest()

    def is_stale(self, max_age_hours: int = 24) -> bool:
        """Check if data item is stale."""
        if not self.indexed_at:
            return True

        age = datetime.now(timezone.utc) - self.indexed_at
        return age.total_seconds() > (max_age_hours * 3600)

class DataNormalizationService:
    """Service for data normalization, search, and content management."""

    def __init__(self):
        self.session: Optional[AsyncSession] = None

        # Search index configuration
        self.search_index = "singlebrief_unified"
        self.elasticsearch_url = "http://localhost:9200"  # Configure as needed

        # Classification models (simplified placeholders)
        self.content_classifiers = {}
        self.topic_models = {}

        # Deduplication thresholds
        self.duplicate_threshold = 0.85
        self.similarity_threshold = 0.75

    async def get_session(self) -> AsyncSession:
        """Get database session."""
        if self.session is None:
            self.session = await get_db_session().__anext__()
        return self.session

    async def normalize_slack_data(self, raw_data: Dict[str, Any]) -> UnifiedDataItem:
        """Normalize Slack data to unified format."""
        try:
            # Extract core information
            source_id = raw_data.get("ts", raw_data.get("id", ""))
            content = raw_data.get("text", "")
            author = raw_data.get("user", raw_data.get("username", ""))

            # Determine content type
            content_type = ContentType.MESSAGE
            if raw_data.get("thread_ts"):
                content_type = ContentType.THREAD

            # Parse timestamps
            created_at = None
            if raw_data.get("ts"):
                try:
                    timestamp = float(raw_data["ts"])
                    created_at = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                except (ValueError, TypeError):
                    pass

            # Extract participants
            participants = []
            if "members" in raw_data:
                participants = raw_data["members"]
            elif author:
                participants = [author]

            # Build unified item
            unified_item = UnifiedDataItem(
                id=f"slack_{source_id}",
                source_type=SourceType.SLACK,
                source_id=source_id,
                content_type=content_type,
                title=None,  # Slack messages don't have titles
                content=content,
                author=author,
                participants=participants,
                created_at=created_at,
                updated_at=created_at,
                source_metadata=raw_data,
                thread_id=raw_data.get("thread_ts"),
                parent_id=raw_data.get("reply_to") or raw_data.get("thread_ts"),
            )

            # Classify and enhance
            await self._classify_content(unified_item)
            await self._calculate_scores(unified_item)

            return unified_item

        except Exception as e:
            logger.error(f"Error normalizing Slack data: {e}")
            raise

    async def normalize_email_data(self, raw_data: Dict[str, Any]) -> UnifiedDataItem:
        """Normalize email data to unified format."""
        try:
            source_id = raw_data.get("id", "")
            subject = raw_data.get("subject", "")
            content = raw_data.get("body", raw_data.get("snippet", ""))

            # Extract sender information
            author = None
            author_email = None
            if "from" in raw_data:
                from_field = raw_data["from"]
                if isinstance(from_field, dict):
                    author = from_field.get("name")
                    author_email = from_field.get("email")
                elif isinstance(from_field, str):
                    # Parse "Name <email>" format
                    match = re.match(r"^(.+?)\s*<(.+?)>$", from_field)
                    if match:
                        author, author_email = match.groups()
                    else:
                        author_email = from_field

            # Parse timestamps
            created_at = None
            if raw_data.get("date"):
                try:
                    created_at = datetime.fromisoformat(
                        raw_data["date"].replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    pass

            # Extract participants
            participants = []
            for field in ["to", "cc", "bcc"]:
                if field in raw_data:
                    recipients = raw_data[field]
                    if isinstance(recipients, list):
                        for recipient in recipients:
                            if isinstance(recipient, dict):
                                participants.append(recipient.get("email", ""))
                            else:
                                participants.append(str(recipient))
                    elif isinstance(recipients, str):
                        participants.append(recipients)

            if author_email:
                participants.append(author_email)

            # Build unified item
            unified_item = UnifiedDataItem(
                id=f"email_{source_id}",
                source_type=(
                    SourceType.GMAIL
                    if "gmail" in raw_data.get("source", "")
                    else SourceType.OUTLOOK
                ),
                source_id=source_id,
                content_type=ContentType.EMAIL,
                title=subject,
                content=content,
                author=author,
                author_email=author_email,
                participants=list(set(participants)),  # Remove duplicates
                created_at=created_at,
                updated_at=created_at,
                source_metadata=raw_data,
                thread_id=raw_data.get("thread_id"),
                parent_id=raw_data.get("in_reply_to"),
            )

            # Classify and enhance
            await self._classify_content(unified_item)
            await self._calculate_scores(unified_item)

            return unified_item

        except Exception as e:
            logger.error(f"Error normalizing email data: {e}")
            raise

    async def normalize_document_data(
        self, raw_data: Dict[str, Any]
    ) -> UnifiedDataItem:
        """Normalize document data to unified format."""
        try:
            source_id = raw_data.get("id", "")
            title = raw_data.get("name", raw_data.get("title", ""))
            content = raw_data.get("content", raw_data.get("description", ""))

            # Extract author information
            author = None
            if "owner" in raw_data:
                owner = raw_data["owner"]
                if isinstance(owner, dict):
                    author = owner.get("displayName", owner.get("name"))
                else:
                    author = str(owner)

            # Parse timestamps
            created_at = None
            updated_at = None
            for field, target in [
                ("createdTime", "created_at"),
                ("modifiedTime", "updated_at"),
            ]:
                if raw_data.get(field):
                    try:
                        timestamp = datetime.fromisoformat(
                            raw_data[field].replace("Z", "+00:00")
                        )
                        if target == "created_at":
                            created_at = timestamp
                        else:
                            updated_at = timestamp
                    except (ValueError, TypeError):
                        pass

            # Extract tags and categories
            tags = []
            categories = []
            if "labels" in raw_data:
                tags.extend(raw_data["labels"])
            if "categories" in raw_data:
                categories.extend(raw_data["categories"])
            if "mimeType" in raw_data:
                categories.append(raw_data["mimeType"])

            # Build unified item
            unified_item = UnifiedDataItem(
                id=f"doc_{source_id}",
                source_type=(
                    SourceType.GDRIVE
                    if "drive" in raw_data.get("source", "")
                    else SourceType.ONEDRIVE
                ),
                source_id=source_id,
                content_type=ContentType.DOCUMENT,
                title=title,
                content=content,
                author=author,
                tags=tags,
                categories=categories,
                created_at=created_at,
                updated_at=updated_at,
                source_metadata=raw_data,
                parent_id=raw_data.get("parent_id", raw_data.get("folder_id")),
            )

            # Classify and enhance
            await self._classify_content(unified_item)
            await self._calculate_scores(unified_item)

            return unified_item

        except Exception as e:
            logger.error(f"Error normalizing document data: {e}")
            raise

    async def normalize_github_data(self, raw_data: Dict[str, Any]) -> UnifiedDataItem:
        """Normalize GitHub data to unified format."""
        try:
            source_id = str(raw_data.get("id", ""))

            # Determine content type
            content_type = ContentType.UNKNOWN
            if "pull_request" in raw_data or raw_data.get("type") == "pull_request":
                content_type = ContentType.PULL_REQUEST
            elif "issue" in raw_data or raw_data.get("type") == "issue":
                content_type = ContentType.ISSUE
            elif "repository" in raw_data or raw_data.get("type") == "repository":
                content_type = ContentType.REPOSITORY

            title = raw_data.get("title", raw_data.get("name", ""))
            content = raw_data.get("body", raw_data.get("description", ""))

            # Extract author information
            author = None
            if "user" in raw_data:
                user = raw_data["user"]
                if isinstance(user, dict):
                    author = user.get("login", user.get("name"))
                else:
                    author = str(user)

            # Parse timestamps
            created_at = None
            updated_at = None
            for field, target in [
                ("created_at", "created_at"),
                ("updated_at", "updated_at"),
            ]:
                if raw_data.get(field):
                    try:
                        timestamp = datetime.fromisoformat(
                            raw_data[field].replace("Z", "+00:00")
                        )
                        if target == "created_at":
                            created_at = timestamp
                        else:
                            updated_at = timestamp
                    except (ValueError, TypeError):
                        pass

            # Extract labels as tags
            tags = []
            if "labels" in raw_data:
                labels = raw_data["labels"]
                if isinstance(labels, list):
                    for label in labels:
                        if isinstance(label, dict):
                            tags.append(label.get("name", ""))
                        else:
                            tags.append(str(label))

            # Build unified item
            unified_item = UnifiedDataItem(
                id=f"github_{source_id}",
                source_type=SourceType.GITHUB,
                source_id=source_id,
                content_type=content_type,
                title=title,
                content=content,
                author=author,
                tags=tags,
                created_at=created_at,
                updated_at=updated_at,
                source_metadata=raw_data,
                parent_id=(
                    raw_data.get("repository", {}).get("id")
                    if isinstance(raw_data.get("repository"), dict)
                    else None
                ),
            )

            # Classify and enhance
            await self._classify_content(unified_item)
            await self._calculate_scores(unified_item)

            return unified_item

        except Exception as e:
            logger.error(f"Error normalizing GitHub data: {e}")
            raise

    async def normalize_jira_data(self, raw_data: Dict[str, Any]) -> UnifiedDataItem:
        """Normalize Jira data to unified format."""
        try:
            source_id = raw_data.get("id", raw_data.get("key", ""))
            title = raw_data.get("summary", "")
            content = raw_data.get("description", "")

            # Extract author information
            author = None
            if "reporter" in raw_data:
                reporter = raw_data["reporter"]
                if isinstance(reporter, dict):
                    author = reporter.get("displayName", reporter.get("name"))
                else:
                    author = str(reporter)

            # Parse timestamps
            created_at = None
            updated_at = None
            for field, target in [("created", "created_at"), ("updated", "updated_at")]:
                if raw_data.get(field):
                    try:
                        timestamp = datetime.fromisoformat(
                            raw_data[field].replace("Z", "+00:00")
                        )
                        if target == "created_at":
                            created_at = timestamp
                        else:
                            updated_at = timestamp
                    except (ValueError, TypeError):
                        pass

            # Extract tags and categories
            tags = []
            categories = []
            if "labels" in raw_data:
                tags.extend(raw_data["labels"])
            if "components" in raw_data:
                for component in raw_data["components"]:
                    if isinstance(component, dict):
                        categories.append(component.get("name", ""))
                    else:
                        categories.append(str(component))

            # Extract status and priority as categories
            if "status" in raw_data:
                status = raw_data["status"]
                if isinstance(status, dict):
                    categories.append(f"status:{status.get('name', '')}")
                else:
                    categories.append(f"status:{status}")

            if "priority" in raw_data:
                priority = raw_data["priority"]
                if isinstance(priority, dict):
                    categories.append(f"priority:{priority.get('name', '')}")
                else:
                    categories.append(f"priority:{priority}")

            # Build unified item
            unified_item = UnifiedDataItem(
                id=f"jira_{source_id}",
                source_type=SourceType.JIRA,
                source_id=source_id,
                content_type=ContentType.ISSUE,
                title=title,
                content=content,
                author=author,
                tags=tags,
                categories=categories,
                created_at=created_at,
                updated_at=updated_at,
                source_metadata=raw_data,
                parent_id=(
                    raw_data.get("project", {}).get("id")
                    if isinstance(raw_data.get("project"), dict)
                    else None
                ),
            )

            # Classify and enhance
            await self._classify_content(unified_item)
            await self._calculate_scores(unified_item)

            return unified_item

        except Exception as e:
            logger.error(f"Error normalizing Jira data: {e}")
            raise

    async def _classify_content(self, item: UnifiedDataItem):
        """Classify content and add tags/categories."""
        try:
            content_text = f"{item.title or ''} {item.content or ''}".strip()
            if not content_text:
                return

            # Simplified classification (in production, use ML models)
            categories = set(item.categories or [])
            tags = set(item.tags or [])

            # Content type classification
            if any(
                word in content_text.lower()
                for word in ["urgent", "asap", "critical", "emergency"]
            ):
                tags.add("urgent")

            if any(
                word in content_text.lower()
                for word in ["meeting", "call", "zoom", "conference"]
            ):
                categories.add("meeting")

            if any(
                word in content_text.lower()
                for word in ["todo", "task", "action item", "follow up"]
            ):
                categories.add("action_item")

            if any(
                word in content_text.lower()
                for word in ["bug", "error", "issue", "problem", "fix"]
            ):
                categories.add("technical_issue")

            if any(
                word in content_text.lower()
                for word in ["project", "milestone", "deadline", "delivery"]
            ):
                categories.add("project_management")

            # Topic modeling (simplified)
            if any(
                word in content_text.lower()
                for word in ["code", "development", "programming", "repository"]
            ):
                categories.add("development")

            if any(
                word in content_text.lower()
                for word in ["design", "ui", "ux", "mockup", "wireframe"]
            ):
                categories.add("design")

            if any(
                word in content_text.lower()
                for word in ["marketing", "campaign", "promotion", "advertising"]
            ):
                categories.add("marketing")

            item.categories = list(categories)
            item.tags = list(tags)
            item.classification_confidence = 0.8  # Placeholder confidence

        except Exception as e:
            logger.error(f"Error classifying content: {e}")

    async def _calculate_scores(self, item: UnifiedDataItem):
        """Calculate relevance, freshness, and quality scores."""
        try:
            # Freshness score (0-1, with 1 being most recent)
            if item.updated_at:
                age_days = (datetime.now(timezone.utc) - item.updated_at).days
                item.freshness_score = max(0, 1 - (age_days / 30))  # Decay over 30 days
            else:
                item.freshness_score = 0.5  # Default for unknown age

            # Quality score based on content completeness and metadata
            quality_factors = []

            # Content quality
            if item.title:
                quality_factors.append(0.2)
            if item.content and len(item.content) > 50:
                quality_factors.append(0.3)
            if item.author:
                quality_factors.append(0.1)
            if item.participants:
                quality_factors.append(0.1)
            if item.tags:
                quality_factors.append(0.1)
            if item.categories:
                quality_factors.append(0.1)
            if item.source_metadata:
                quality_factors.append(0.1)

            item.quality_score = sum(quality_factors)

            # Base relevance score (will be adjusted based on search context)
            item.relevance_score = item.freshness_score * 0.3 + item.quality_score * 0.7

        except Exception as e:
            logger.error(f"Error calculating scores: {e}")

    async def detect_duplicates(
        self, items: List[UnifiedDataItem]
    ) -> Dict[str, List[str]]:
        """Detect duplicate items using content similarity."""
        try:
            duplicates = {}
            processed_hashes = {}

            for item in items:
                content_hash = item.content_hash()

                # Check for exact content matches
                if content_hash in processed_hashes:
                    original_id = processed_hashes[content_hash]
                    if original_id not in duplicates:
                        duplicates[original_id] = []
                    duplicates[original_id].append(item.id)
                    item.duplicate_of = original_id
                    item.duplicate_confidence = 1.0
                else:
                    processed_hashes[content_hash] = item.id

                # Check for fuzzy duplicates (simplified implementation)
                if not item.duplicate_of:
                    for existing_hash, existing_id in processed_hashes.items():
                        if existing_id != item.id:
                            similarity = await self._calculate_content_similarity(
                                content_hash, existing_hash
                            )
                            if similarity > self.duplicate_threshold:
                                if existing_id not in duplicates:
                                    duplicates[existing_id] = []
                                duplicates[existing_id].append(item.id)
                                item.duplicate_of = existing_id
                                item.duplicate_confidence = similarity
                                break

            return duplicates

        except Exception as e:
            logger.error(f"Error detecting duplicates: {e}")
            return {}

    async def _calculate_content_similarity(self, hash1: str, hash2: str) -> float:
        """Calculate similarity between two content hashes (simplified)."""
        # In production, use proper text similarity algorithms
        # like TF-IDF cosine similarity, semantic embeddings, etc.

        # Simple character-based similarity for now
        common_chars = sum(c1 == c2 for c1, c2 in zip(hash1, hash2))
        return common_chars / max(len(hash1), len(hash2))

    async def index_to_search_engine(self, items: List[UnifiedDataItem]) -> bool:
        """Index items to Elasticsearch/OpenSearch."""
        try:
            if not items:
                return True

            # Prepare bulk indexing data
            bulk_data = []
            for item in items:
                # Create index action
                action = {"index": {"_index": self.search_index, "_id": item.id}}
                bulk_data.append(json.dumps(action))
                bulk_data.append(json.dumps(item.to_dict()))

            # Send to Elasticsearch
            bulk_body = "\n".join(bulk_data) + "\n"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.elasticsearch_url}/_bulk",
                    data=bulk_body,
                    headers={"Content-Type": "application/x-ndjson"},
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("errors"):
                            logger.warning(f"Some items failed to index: {result}")
                        return True
                    else:
                        logger.error(f"Failed to index items: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Error indexing to search engine: {e}")
            return False

    async def search_unified_data(
        self,
        query: str,
        content_types: Optional[List[ContentType]] = None,
        source_types: Optional[List[SourceType]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        tags: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Search unified data across all sources."""
        try:
            # Build Elasticsearch query
            search_query = {
                "query": {"bool": {"must": [], "filter": []}},
                "sort": [
                    {"relevance_score": {"order": "desc"}},
                    {"freshness_score": {"order": "desc"}},
                    {"updated_at": {"order": "desc"}},
                ],
                "from": offset,
                "size": limit,
                "highlight": {"fields": {"content": {}, "title": {}}},
            }

            # Add text search
            if query:
                search_query["query"]["bool"]["must"].append(
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^2", "content", "summary"],
                            "type": "best_fields",
                            "fuzziness": "AUTO",
                        }
                    }
                )

            # Add filters
            if content_types:
                search_query["query"]["bool"]["filter"].append(
                    {"terms": {"content_type": [ct.value for ct in content_types]}}
                )

            if source_types:
                search_query["query"]["bool"]["filter"].append(
                    {"terms": {"source_type": [st.value for st in source_types]}}
                )

            if date_range:
                start_date, end_date = date_range
                search_query["query"]["bool"]["filter"].append(
                    {
                        "range": {
                            "updated_at": {
                                "gte": start_date.isoformat(),
                                "lte": end_date.isoformat(),
                            }
                        }
                    }
                )

            if tags:
                search_query["query"]["bool"]["filter"].append(
                    {"terms": {"tags": tags}}
                )

            if categories:
                search_query["query"]["bool"]["filter"].append(
                    {"terms": {"categories": categories}}
                )

            # Execute search
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.elasticsearch_url}/{self.search_index}/_search",
                    json=search_query,
                ) as response:
                    if response.status == 200:
                        result = await response.json()

                        # Process results
                        hits = result.get("hits", {})
                        total = hits.get("total", {})
                        if isinstance(total, dict):
                            total_count = total.get("value", 0)
                        else:
                            total_count = total

                        items = []
                        for hit in hits.get("hits", []):
                            source_data = hit["_source"]

                            # Add search metadata
                            source_data["search_score"] = hit["_score"]
                            if "highlight" in hit:
                                source_data["highlights"] = hit["highlight"]

                            items.append(source_data)

                        return {
                            "total": total_count,
                            "items": items,
                            "offset": offset,
                            "limit": limit,
                            "query": query,
                        }
                    else:
                        logger.error(f"Search failed: {response.status}")
                        return {"total": 0, "items": [], "error": "Search failed"}

        except Exception as e:
            logger.error(f"Error searching unified data: {e}")
            return {"total": 0, "items": [], "error": str(e)}

    async def get_aggregated_stats(self) -> Dict[str, Any]:
        """Get aggregated statistics about indexed data."""
        try:
            agg_query = {
                "size": 0,
                "aggs": {
                    "by_content_type": {"terms": {"field": "content_type"}},
                    "by_source_type": {"terms": {"field": "source_type"}},
                    "by_category": {"terms": {"field": "categories", "size": 20}},
                    "by_author": {"terms": {"field": "author.keyword", "size": 10}},
                    "freshness_distribution": {
                        "histogram": {"field": "freshness_score", "interval": 0.1}
                    },
                    "recent_activity": {
                        "date_histogram": {
                            "field": "updated_at",
                            "calendar_interval": "day",
                            "min_doc_count": 1,
                        }
                    },
                },
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.elasticsearch_url}/{self.search_index}/_search",
                    json=agg_query,
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        aggregations = result.get("aggregations", {})

                        return {
                            "total_documents": result.get("hits", {})
                            .get("total", {})
                            .get("value", 0),
                            "content_types": aggregations.get(
                                "by_content_type", {}
                            ).get("buckets", []),
                            "source_types": aggregations.get("by_source_type", {}).get(
                                "buckets", []
                            ),
                            "top_categories": aggregations.get("by_category", {}).get(
                                "buckets", []
                            ),
                            "top_authors": aggregations.get("by_author", {}).get(
                                "buckets", []
                            ),
                            "freshness_distribution": aggregations.get(
                                "freshness_distribution", {}
                            ).get("buckets", []),
                            "recent_activity": aggregations.get(
                                "recent_activity", {}
                            ).get("buckets", []),
                        }
                    else:
                        logger.error(f"Stats query failed: {response.status}")
                        return {}

        except Exception as e:
            logger.error(f"Error getting aggregated stats: {e}")
            return {}

    async def cleanup_stale_data(self, max_age_days: int = 90) -> int:
        """Remove stale data from the search index."""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)

            delete_query = {
                "query": {"range": {"indexed_at": {"lt": cutoff_date.isoformat()}}}
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.elasticsearch_url}/{self.search_index}/_delete_by_query",
                    json=delete_query,
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        deleted_count = result.get("deleted", 0)
                        logger.info(f"Cleaned up {deleted_count} stale documents")
                        return deleted_count
                    else:
                        logger.error(f"Cleanup failed: {response.status}")
                        return 0

        except Exception as e:
            logger.error(f"Error cleaning up stale data: {e}")
            return 0

    async def reindex_all_data(self) -> bool:
        """Reindex all data from sources."""
        try:
            # This would typically involve:
            # 1. Fetching fresh data from all integrations
            # 2. Normalizing the data
            # 3. Detecting duplicates
            # 4. Indexing to search engine

            # For now, return success placeholder
            logger.info("Reindexing all data (placeholder implementation)")
            return True

        except Exception as e:
            logger.error(f"Error reindexing data: {e}")
            return False

# Global service instance
data_normalization_service = DataNormalizationService()
