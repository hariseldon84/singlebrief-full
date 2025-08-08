"""
Memory Lifecycle Management for SingleBrief AI System
Handles memory expiration, archival, compression, and cleanup operations
"""

from typing import Any, Dict, List, Optional, Tuple

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, or_, text
from sqlalchemy.orm import Session

from app.ai.memory_service import memory_service
from app.core.database import get_db_session
from app.models.memory import (Conversation, ConversationMessage, Decision,
                               MemoryEmbedding, TeamMemory, UserMemory)

logger = logging.getLogger(__name__)

class MemoryLifecycleManager:
    """Manages memory lifecycle including expiration, archival, and cleanup"""

    def __init__(self):
        self.memory_service = memory_service

    async def apply_expiration_policies(
        self, db: Session, organization_id: Optional[str] = None, dry_run: bool = False
    ) -> Dict[str, Any]:
        """Apply memory expiration policies based on retention settings"""
        try:
            # Define retention policies (in days)
            retention_policies = {
                "standard": 90,  # 3 months
                "extended": 365,  # 1 year
                "permanent": None,  # No expiration
                "delete_on_request": 1,  # 1 day grace period
            }

            expired_counts = {
                "user_memories": 0,
                "team_memories": 0,
                "conversations": 0,
                "total_items": 0,
            }

            current_time = datetime.now(timezone.utc)

            # Process each retention policy
            for policy, days in retention_policies.items():
                if days is None:  # Permanent retention
                    continue

                cutoff_date = current_time - timedelta(days=days)

                # Query expired user memories
                user_memory_query = db.query(UserMemory).filter(
                    UserMemory.created_at < cutoff_date, UserMemory.is_active == True
                )

                if organization_id:
                    user_memory_query = user_memory_query.filter(
                        UserMemory.organization_id == organization_id
                    )

                # Handle retention policy specific logic
                if policy == "delete_on_request":
                    # Only expire memories explicitly marked for deletion
                    user_memory_query = user_memory_query.filter(
                        UserMemory.memory_metadata.op("->>")("deletion_requested")
                        == "true"
                    )

                expired_user_memories = user_memory_query.all()

                # Query expired team memories
                team_memory_query = db.query(TeamMemory).filter(
                    TeamMemory.created_at < cutoff_date, TeamMemory.is_active == True
                )

                if organization_id:
                    team_memory_query = team_memory_query.filter(
                        TeamMemory.organization_id == organization_id
                    )

                if policy == "delete_on_request":
                    team_memory_query = team_memory_query.filter(
                        TeamMemory.team_metadata.op("->>")("deletion_requested")
                        == "true"
                    )

                expired_team_memories = team_memory_query.all()

                # Query expired conversations
                conversation_query = db.query(Conversation).filter(
                    Conversation.created_at < cutoff_date,
                    Conversation.retention_policy == policy,
                    Conversation.is_archived == False,
                )

                if organization_id:
                    conversation_query = conversation_query.filter(
                        Conversation.organization_id == organization_id
                    )

                expired_conversations = conversation_query.all()

                # Apply expiration actions
                if not dry_run:
                    # Expire user memories
                    for memory in expired_user_memories:
                        await self._expire_user_memory(db, memory)
                        expired_counts["user_memories"] += 1

                    # Expire team memories
                    for memory in expired_team_memories:
                        await self._expire_team_memory(db, memory)
                        expired_counts["team_memories"] += 1

                    # Archive conversations
                    for conversation in expired_conversations:
                        await self._archive_conversation(db, conversation)
                        expired_counts["conversations"] += 1

                    db.commit()
                else:
                    # Count items that would be expired
                    expired_counts["user_memories"] += len(expired_user_memories)
                    expired_counts["team_memories"] += len(expired_team_memories)
                    expired_counts["conversations"] += len(expired_conversations)

            expired_counts["total_items"] = (
                expired_counts["user_memories"]
                + expired_counts["team_memories"]
                + expired_counts["conversations"]
            )

            result = {
                "operation": "apply_expiration_policies",
                "organization_id": organization_id,
                "dry_run": dry_run,
                "expired_counts": expired_counts,
                "policies_applied": list(retention_policies.keys()),
                "processed_at": current_time.isoformat(),
            }

            logger.info(
                f"Applied expiration policies: {expired_counts['total_items']} items processed"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to apply expiration policies: {e}")
            if not dry_run:
                db.rollback()
            raise

    async def _expire_user_memory(self, db: Session, memory: UserMemory):
        """Expire a user memory and its associated embeddings"""
        try:
            # Delete vector embedding
            await self.memory_service.delete_memory_embedding(
                db, memory.id, "user_memory"
            )

            # Mark memory as inactive instead of deleting
            memory.is_active = False
            memory.expires_at = datetime.now(timezone.utc)
            memory.updated_at = datetime.now(timezone.utc)

            logger.debug(f"Expired user memory {memory.id}")

        except Exception as e:
            logger.error(f"Failed to expire user memory {memory.id}: {e}")
            raise

    async def _expire_team_memory(self, db: Session, memory: TeamMemory):
        """Expire a team memory and its associated embeddings"""
        try:
            # Delete vector embedding
            await self.memory_service.delete_memory_embedding(
                db, memory.id, "team_memory"
            )

            # Mark memory as inactive instead of deleting
            memory.is_active = False
            memory.expires_at = datetime.now(timezone.utc)
            memory.updated_at = datetime.now(timezone.utc)

            logger.debug(f"Expired team memory {memory.id}")

        except Exception as e:
            logger.error(f"Failed to expire team memory {memory.id}: {e}")
            raise

    async def _archive_conversation(self, db: Session, conversation: Conversation):
        """Archive a conversation and compress its messages"""
        try:
            # Mark conversation as archived
            conversation.is_archived = True
            conversation.updated_at = datetime.now(timezone.utc)

            # Optionally compress conversation messages
            message_count = (
                db.query(ConversationMessage)
                .filter(ConversationMessage.conversation_id == conversation.id)
                .count()
            )

            if message_count > 10:  # Compress conversations with many messages
                await self._compress_conversation_messages(db, conversation.id)

            logger.debug(f"Archived conversation {conversation.id}")

        except Exception as e:
            logger.error(f"Failed to archive conversation {conversation.id}: {e}")
            raise

    async def _compress_conversation_messages(self, db: Session, conversation_id: str):
        """Compress conversation messages by summarizing content"""
        try:
            # Get all messages for the conversation
            messages = (
                db.query(ConversationMessage)
                .filter(ConversationMessage.conversation_id == conversation_id)
                .order_by(ConversationMessage.sequence_number)
                .all()
            )

            if len(messages) <= 5:  # Don't compress short conversations
                return

            # Create a compressed summary (mock implementation)
            # In production, this would use LLM to summarize the conversation
            summary_content = (
                f"Conversation summary: {len(messages)} messages exchanged"
            )

            # Keep first and last few messages, replace middle with summary
            keep_start = 2
            keep_end = 2

            if len(messages) > keep_start + keep_end + 1:
                # Create summary message
                middle_index = keep_start + (len(messages) - keep_start - keep_end) // 2

                summary_message = ConversationMessage(
                    conversation_id=conversation_id,
                    message_type="system_message",
                    content=summary_content,
                    sequence_number=middle_index,
                    message_metadata={
                        "compressed": True,
                        "original_message_count": len(messages) - keep_start - keep_end,
                        "compression_date": datetime.now(timezone.utc).isoformat(),
                    },
                )

                # Remove middle messages and add summary
                for i in range(keep_start, len(messages) - keep_end):
                    if i != middle_index:
                        db.delete(messages[i])

                db.add(summary_message)

            logger.debug(f"Compressed conversation {conversation_id}")

        except Exception as e:
            logger.error(f"Failed to compress conversation {conversation_id}: {e}")
            raise

    async def cleanup_orphaned_embeddings(
        self, db: Session, organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Clean up orphaned vector embeddings"""
        try:
            cleanup_counts = {"orphaned_embeddings": 0, "vector_ids_cleaned": []}

            # Find embeddings without corresponding memories
            orphaned_embeddings = (
                db.query(MemoryEmbedding)
                .filter(
                    and_(
                        or_(
                            and_(
                                MemoryEmbedding.user_memory_id.isnot(None),
                                ~db.query(UserMemory)
                                .filter(UserMemory.id == MemoryEmbedding.user_memory_id)
                                .exists(),
                            ),
                            and_(
                                MemoryEmbedding.team_memory_id.isnot(None),
                                ~db.query(TeamMemory)
                                .filter(TeamMemory.id == MemoryEmbedding.team_memory_id)
                                .exists(),
                            ),
                        )
                    )
                )
                .all()
            )

            # Clean up orphaned embeddings
            for embedding in orphaned_embeddings:
                try:
                    # Delete from vector database
                    await self.memory_service.vector_db.delete_memory_embedding(
                        embedding.vector_id
                    )

                    # Delete embedding record
                    db.delete(embedding)

                    cleanup_counts["orphaned_embeddings"] += 1
                    cleanup_counts["vector_ids_cleaned"].append(embedding.vector_id)

                except Exception as e:
                    logger.warning(f"Failed to clean embedding {embedding.id}: {e}")
                    continue

            db.commit()

            result = {
                "operation": "cleanup_orphaned_embeddings",
                "organization_id": organization_id,
                "cleanup_counts": cleanup_counts,
                "cleaned_at": datetime.now(timezone.utc).isoformat(),
            }

            logger.info(
                f"Cleaned up {cleanup_counts['orphaned_embeddings']} orphaned embeddings"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to cleanup orphaned embeddings: {e}")
            db.rollback()
            raise

    async def optimize_memory_storage(
        self, db: Session, organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Optimize memory storage by analyzing and improving performance"""
        try:
            optimization_results = {
                "duplicates_merged": 0,
                "low_importance_archived": 0,
                "unused_memories_marked": 0,
                "storage_freed_mb": 0.0,
            }

            # Find and merge duplicate memories
            duplicates_merged = await self._merge_duplicate_memories(
                db, organization_id
            )
            optimization_results["duplicates_merged"] = duplicates_merged

            # Archive low-importance, old memories
            archived_count = await self._archive_low_importance_memories(
                db, organization_id
            )
            optimization_results["low_importance_archived"] = archived_count

            # Mark unused memories
            unused_count = await self._mark_unused_memories(db, organization_id)
            optimization_results["unused_memories_marked"] = unused_count

            # Estimate storage freed (mock calculation)
            total_items = duplicates_merged + archived_count + unused_count
            optimization_results["storage_freed_mb"] = (
                total_items * 0.5
            )  # Rough estimate

            db.commit()

            result = {
                "operation": "optimize_memory_storage",
                "organization_id": organization_id,
                "optimization_results": optimization_results,
                "optimized_at": datetime.now(timezone.utc).isoformat(),
            }

            logger.info(f"Optimized memory storage: {total_items} items processed")
            return result

        except Exception as e:
            logger.error(f"Failed to optimize memory storage: {e}")
            db.rollback()
            raise

    async def _merge_duplicate_memories(
        self, db: Session, organization_id: Optional[str] = None
    ) -> int:
        """Find and merge duplicate memories based on content similarity"""
        try:
            # This is a simplified implementation
            # In production, this would use semantic similarity via vector search

            merged_count = 0

            # Find user memories with similar content
            user_memories = db.query(UserMemory).filter(UserMemory.is_active == True)

            if organization_id:
                user_memories = user_memories.filter(
                    UserMemory.organization_id == organization_id
                )

            user_memories = user_memories.all()

            # Group by user and category for duplicate detection
            user_groups = {}
            for memory in user_memories:
                key = f"{memory.user_id}_{memory.category}"
                if key not in user_groups:
                    user_groups[key] = []
                user_groups[key].append(memory)

            # Find potential duplicates within each group
            for group_memories in user_groups.values():
                if len(group_memories) > 1:
                    # Sort by importance and keep the most important one
                    group_memories.sort(key=lambda m: m.importance_score, reverse=True)
                    primary_memory = group_memories[0]

                    for duplicate in group_memories[1:]:
                        # Check if content is very similar (basic check)
                        if (
                            self._calculate_content_similarity(
                                primary_memory.content, duplicate.content
                            )
                            > 0.8
                        ):
                            # Merge metadata and mark duplicate as inactive
                            await self._merge_memory_metadata(primary_memory, duplicate)
                            duplicate.is_active = False
                            duplicate.updated_at = datetime.now(timezone.utc)
                            merged_count += 1

            return merged_count

        except Exception as e:
            logger.error(f"Failed to merge duplicate memories: {e}")
            return 0

    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate basic content similarity (simplified implementation)"""
        # This is a very basic similarity calculation
        # In production, use proper text similarity algorithms
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())

        if not words1 and not words2:
            return 1.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    async def _merge_memory_metadata(self, primary: UserMemory, duplicate: UserMemory):
        """Merge metadata from duplicate memory into primary memory"""
        try:
            # Merge metadata
            primary_meta = primary.memory_metadata or {}
            duplicate_meta = duplicate.memory_metadata or {}

            # Add merged flag and original memory info
            primary_meta["merged_memories"] = primary_meta.get("merged_memories", [])
            primary_meta["merged_memories"].append(
                {
                    "memory_id": duplicate.id,
                    "merged_at": datetime.now(timezone.utc).isoformat(),
                    "original_content": (
                        duplicate.content[:100] + "..."
                        if len(duplicate.content) > 100
                        else duplicate.content
                    ),
                }
            )

            # Update importance score to average
            primary.importance_score = (
                primary.importance_score + duplicate.importance_score
            ) / 2
            primary.memory_metadata = primary_meta
            primary.updated_at = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Failed to merge memory metadata: {e}")
            raise

    async def _archive_low_importance_memories(
        self, db: Session, organization_id: Optional[str] = None
    ) -> int:
        """Archive memories with low importance that haven't been accessed recently"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=60)
            archived_count = 0

            # Find low-importance user memories
            low_importance_memories = db.query(UserMemory).filter(
                UserMemory.importance_score < 0.3,
                UserMemory.is_active == True,
                or_(
                    UserMemory.last_accessed_at < cutoff_date,
                    UserMemory.last_accessed_at.is_(None),
                ),
                UserMemory.access_count < 5,
            )

            if organization_id:
                low_importance_memories = low_importance_memories.filter(
                    UserMemory.organization_id == organization_id
                )

            for memory in low_importance_memories.all():
                memory.is_active = False
                memory.memory_metadata = memory.memory_metadata or {}
                memory.memory_metadata["archived_reason"] = "low_importance_low_usage"
                memory.memory_metadata["archived_at"] = datetime.now(
                    timezone.utc
                ).isoformat()
                memory.updated_at = datetime.now(timezone.utc)
                archived_count += 1

            return archived_count

        except Exception as e:
            logger.error(f"Failed to archive low importance memories: {e}")
            return 0

    async def _mark_unused_memories(
        self, db: Session, organization_id: Optional[str] = None
    ) -> int:
        """Mark memories as potentially unused based on access patterns"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)
            marked_count = 0

            # Find memories that haven't been accessed in a long time
            unused_memories = db.query(UserMemory).filter(
                UserMemory.is_active == True,
                or_(
                    UserMemory.last_accessed_at < cutoff_date,
                    UserMemory.last_accessed_at.is_(None),
                ),
                UserMemory.access_count == 0,
            )

            if organization_id:
                unused_memories = unused_memories.filter(
                    UserMemory.organization_id == organization_id
                )

            for memory in unused_memories.all():
                memory.memory_metadata = memory.memory_metadata or {}
                memory.memory_metadata["potentially_unused"] = True
                memory.memory_metadata["marked_unused_at"] = datetime.now(
                    timezone.utc
                ).isoformat()
                memory.updated_at = datetime.now(timezone.utc)
                marked_count += 1

            return marked_count

        except Exception as e:
            logger.error(f"Failed to mark unused memories: {e}")
            return 0

    async def generate_memory_usage_report(
        self, db: Session, organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive memory usage report"""
        try:
            # Base queries
            user_memory_query = db.query(UserMemory)
            team_memory_query = db.query(TeamMemory)
            conversation_query = db.query(Conversation)

            if organization_id:
                user_memory_query = user_memory_query.filter(
                    UserMemory.organization_id == organization_id
                )
                team_memory_query = team_memory_query.filter(
                    TeamMemory.organization_id == organization_id
                )
                conversation_query = conversation_query.filter(
                    Conversation.organization_id == organization_id
                )

            # Count statistics
            total_user_memories = user_memory_query.count()
            active_user_memories = user_memory_query.filter(
                UserMemory.is_active == True
            ).count()
            total_team_memories = team_memory_query.count()
            active_team_memories = team_memory_query.filter(
                TeamMemory.is_active == True
            ).count()
            total_conversations = conversation_query.count()
            archived_conversations = conversation_query.filter(
                Conversation.is_archived == True
            ).count()

            # Memory type distribution
            memory_types = (
                db.query(
                    UserMemory.memory_type, func.count(UserMemory.id).label("count")
                )
                .filter(UserMemory.is_active == True)
                .group_by(UserMemory.memory_type)
                .all()
            )

            # Category distribution
            categories = (
                db.query(UserMemory.category, func.count(UserMemory.id).label("count"))
                .filter(UserMemory.is_active == True)
                .group_by(UserMemory.category)
                .all()
            )

            # Importance distribution
            importance_ranges = {
                "high": user_memory_query.filter(
                    UserMemory.importance_score >= 0.7, UserMemory.is_active == True
                ).count(),
                "medium": user_memory_query.filter(
                    and_(
                        UserMemory.importance_score >= 0.3,
                        UserMemory.importance_score < 0.7,
                    ),
                    UserMemory.is_active == True,
                ).count(),
                "low": user_memory_query.filter(
                    UserMemory.importance_score < 0.3, UserMemory.is_active == True
                ).count(),
            }

            report = {
                "organization_id": organization_id,
                "report_generated_at": datetime.now(timezone.utc).isoformat(),
                "summary": {
                    "total_user_memories": total_user_memories,
                    "active_user_memories": active_user_memories,
                    "total_team_memories": total_team_memories,
                    "active_team_memories": active_team_memories,
                    "total_conversations": total_conversations,
                    "archived_conversations": archived_conversations,
                },
                "distributions": {
                    "memory_types": {mt.memory_type: mt.count for mt in memory_types},
                    "categories": {cat.category: cat.count for cat in categories},
                    "importance_ranges": importance_ranges,
                },
                "health_metrics": {
                    "active_memory_ratio": (
                        active_user_memories / total_user_memories
                        if total_user_memories > 0
                        else 0
                    ),
                    "archive_ratio": (
                        archived_conversations / total_conversations
                        if total_conversations > 0
                        else 0
                    ),
                    "avg_importance": db.query(func.avg(UserMemory.importance_score))
                    .filter(UserMemory.is_active == True)
                    .scalar()
                    or 0,
                },
            }

            logger.info(
                f"Generated memory usage report for organization {organization_id}"
            )
            return report

        except Exception as e:
            logger.error(f"Failed to generate memory usage report: {e}")
            raise

# Global memory lifecycle manager instance
memory_lifecycle_manager = MemoryLifecycleManager()
