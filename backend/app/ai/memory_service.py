"""
Memory Service for SingleBrief AI System
Handles memory operations, embedding generation, and semantic search
"""

from typing import Any, Dict, List, Optional, Tuple

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.ai.vector_database import vector_db_manager
from app.core.database import get_db_session
from app.models.memory import (Conversation, ConversationMessage, Decision,
                               MemoryEmbedding, TeamMemory, UserMemory)

logger = logging.getLogger(__name__)

class MemoryService:
    """Service for managing memory operations and embeddings"""

    def __init__(self):
        self.vector_db = vector_db_manager

    async def initialize(self) -> bool:
        """Initialize the memory service and vector database"""
        return await self.vector_db.initialize()

    async def create_user_memory(
        self,
        db: Session,
        user_id: str,
        organization_id: str,
        memory_type: str,
        category: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        importance_score: float = 0.5,
        confidence_level: float = 0.5,
        source: str = "conversation",
    ) -> UserMemory:
        """Create a new user memory with vector embedding"""
        try:
            # Create memory record
            user_memory = UserMemory(
                user_id=user_id,
                organization_id=organization_id,
                memory_type=memory_type,
                category=category,
                content=content,
                memory_metadata=metadata or {},
                importance_score=importance_score,
                confidence_level=confidence_level,
                source=source,
            )

            db.add(user_memory)
            db.commit()
            db.refresh(user_memory)

            # Create vector embedding
            vector_id = await self.vector_db.create_memory_embedding(user_memory)

            if vector_id:
                # Store embedding reference
                memory_embedding = MemoryEmbedding(
                    user_memory_id=user_memory.id,
                    embedding_model="text-embedding-ada-002",
                    embedding_version="1.0",
                    content_hash=self.vector_db.db.embedding_generator.get_content_hash(
                        content
                    ),
                    vector_id=vector_id,
                    vector_database=self.vector_db.database_type,
                )

                db.add(memory_embedding)
                db.commit()

            logger.info(f"Created user memory {user_memory.id} with embedding")
            return user_memory

        except Exception as e:
            logger.error(f"Failed to create user memory: {e}")
            db.rollback()
            raise

    async def create_team_memory(
        self,
        db: Session,
        team_id: str,
        organization_id: str,
        created_by_user_id: str,
        memory_type: str,
        category: str,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        importance_score: float = 0.5,
        source: str = "team_discussion",
    ) -> TeamMemory:
        """Create a new team memory with vector embedding"""
        try:
            # Create memory record
            team_memory = TeamMemory(
                team_id=team_id,
                organization_id=organization_id,
                created_by_user_id=created_by_user_id,
                memory_type=memory_type,
                category=category,
                title=title,
                content=content,
                team_metadata=metadata or {},
                importance_score=importance_score,
                source=source,
            )

            db.add(team_memory)
            db.commit()
            db.refresh(team_memory)

            # Create vector embedding
            vector_id = await self.vector_db.create_memory_embedding(team_memory)

            if vector_id:
                # Store embedding reference
                memory_embedding = MemoryEmbedding(
                    team_memory_id=team_memory.id,
                    embedding_model="text-embedding-ada-002",
                    embedding_version="1.0",
                    content_hash=self.vector_db.db.embedding_generator.get_content_hash(
                        content
                    ),
                    vector_id=vector_id,
                    vector_database=self.vector_db.database_type,
                )

                db.add(memory_embedding)
                db.commit()

            logger.info(f"Created team memory {team_memory.id} with embedding")
            return team_memory

        except Exception as e:
            logger.error(f"Failed to create team memory: {e}")
            db.rollback()
            raise

    async def search_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        team_id: Optional[str] = None,
        memory_types: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        limit: int = 10,
        min_similarity: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """Search for relevant memories using semantic similarity"""
        try:
            # Search vector database
            similar_memories = await self.vector_db.search_similar_memories(
                query=query,
                user_id=user_id,
                team_id=team_id,
                limit=limit,
                min_similarity=min_similarity,
            )

            # Filter by memory types and categories if specified
            filtered_memories = []
            for memory in similar_memories:
                if memory_types and memory.get("memory_type") not in memory_types:
                    continue
                if categories and memory.get("category") not in categories:
                    continue
                filtered_memories.append(memory)

            logger.info(f"Found {len(filtered_memories)} relevant memories for query")
            return filtered_memories

        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []

    async def get_conversation_context(
        self, db: Session, user_id: str, query: str, max_items: int = 5
    ) -> Dict[str, Any]:
        """Get relevant conversation context for a query"""
        try:
            # Search for relevant memories
            relevant_memories = await self.search_memories(
                query=query, user_id=user_id, limit=max_items, min_similarity=0.6
            )

            # Get recent conversations
            recent_conversations = (
                db.query(Conversation)
                .filter(Conversation.user_id == user_id)
                .order_by(Conversation.last_activity_at.desc())
                .limit(3)
                .all()
            )

            # Get recent decisions
            recent_decisions = (
                db.query(Decision)
                .filter(Decision.user_id == user_id)
                .order_by(Decision.decided_at.desc())
                .limit(3)
                .all()
            )

            context = {
                "relevant_memories": relevant_memories,
                "recent_conversations": [
                    {
                        "id": conv.id,
                        "title": conv.title,
                        "context_type": conv.context_type,
                        "last_activity": conv.last_activity_at.isoformat(),
                    }
                    for conv in recent_conversations
                ],
                "recent_decisions": [
                    {
                        "id": decision.id,
                        "title": decision.title,
                        "type": decision.decision_type,
                        "status": decision.status,
                        "decided_at": decision.decided_at.isoformat(),
                    }
                    for decision in recent_decisions
                ],
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

            logger.info(
                f"Generated conversation context with {len(relevant_memories)} memories"
            )
            return context

        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            return {"error": str(e)}

    async def update_memory_embedding(
        self, db: Session, memory_id: str, memory_type: str
    ) -> bool:
        """Update vector embedding for a memory"""
        try:
            # Get memory record
            if memory_type == "user_memory":
                memory = db.query(UserMemory).filter(UserMemory.id == memory_id).first()
            else:
                memory = db.query(TeamMemory).filter(TeamMemory.id == memory_id).first()

            if not memory:
                logger.warning(f"Memory {memory_id} not found")
                return False

            # Get existing embedding
            embedding = (
                db.query(MemoryEmbedding)
                .filter(
                    MemoryEmbedding.user_memory_id == memory_id
                    if memory_type == "user_memory"
                    else MemoryEmbedding.team_memory_id == memory_id
                )
                .first()
            )

            if not embedding:
                logger.warning(f"Embedding for memory {memory_id} not found")
                return False

            # Update vector embedding
            success = await self.vector_db.update_memory_embedding(
                vector_id=embedding.vector_id, memory=memory
            )

            if success:
                # Update content hash
                embedding.content_hash = (
                    self.vector_db.db.embedding_generator.get_content_hash(
                        memory.content
                    )
                )
                embedding.updated_at = datetime.now(timezone.utc)
                db.commit()

            logger.info(f"Updated embedding for memory {memory_id}")
            return success

        except Exception as e:
            logger.error(f"Failed to update memory embedding: {e}")
            return False

    async def delete_memory_embedding(
        self, db: Session, memory_id: str, memory_type: str
    ) -> bool:
        """Delete vector embedding for a memory"""
        try:
            # Get embedding record
            embedding = (
                db.query(MemoryEmbedding)
                .filter(
                    MemoryEmbedding.user_memory_id == memory_id
                    if memory_type == "user_memory"
                    else MemoryEmbedding.team_memory_id == memory_id
                )
                .first()
            )

            if not embedding:
                logger.warning(f"Embedding for memory {memory_id} not found")
                return False

            # Delete from vector database
            success = await self.vector_db.delete_memory_embedding(embedding.vector_id)

            if success:
                # Delete embedding record
                db.delete(embedding)
                db.commit()

            logger.info(f"Deleted embedding for memory {memory_id}")
            return success

        except Exception as e:
            logger.error(f"Failed to delete memory embedding: {e}")
            return False

    async def analyze_memory_patterns(
        self, db: Session, user_id: str, days: int = 30
    ) -> Dict[str, Any]:
        """Analyze user memory patterns and generate insights"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            # Get user memories from the period
            user_memories = (
                db.query(UserMemory)
                .filter(
                    UserMemory.user_id == user_id,
                    UserMemory.created_at >= cutoff_date,
                    UserMemory.is_active == True,
                )
                .all()
            )

            # Analyze patterns
            memory_by_type = {}
            memory_by_category = {}
            total_importance = 0

            for memory in user_memories:
                # Group by type
                if memory.memory_type not in memory_by_type:
                    memory_by_type[memory.memory_type] = 0
                memory_by_type[memory.memory_type] += 1

                # Group by category
                if memory.category not in memory_by_category:
                    memory_by_category[memory.category] = 0
                memory_by_category[memory.category] += 1

                total_importance += memory.importance_score

            analysis = {
                "period_days": days,
                "total_memories": len(user_memories),
                "average_importance": (
                    total_importance / len(user_memories) if user_memories else 0
                ),
                "memory_types": memory_by_type,
                "memory_categories": memory_by_category,
                "most_common_type": (
                    max(memory_by_type.items(), key=lambda x: x[1])[0]
                    if memory_by_type
                    else None
                ),
                "most_common_category": (
                    max(memory_by_category.items(), key=lambda x: x[1])[0]
                    if memory_by_category
                    else None
                ),
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
            }

            logger.info(f"Analyzed {len(user_memories)} memories for user {user_id}")
            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze memory patterns: {e}")
            return {"error": str(e)}

# Global memory service instance
memory_service = MemoryService()
