"""
Context Retrieval System for SingleBrief AI
Handles cross-session context retrieval, relevance scoring, and memory aggregation
"""

from typing import Any, Dict, List, Optional, Tuple

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.ai.memory_service import memory_service
from app.models.memory import (Conversation, ConversationMessage, Decision,
                               MemoryEmbedding, TeamMemory, UserMemory)

logger = logging.getLogger(__name__)

class ContextRetrievalService:
    """Service for retrieving and aggregating relevant context across sessions"""

    def __init__(self):
        self.memory_service = memory_service

    async def get_cross_session_context(
        self,
        db: Session,
        user_id: str,
        query: str,
        session_id: Optional[str] = None,
        max_memories: int = 10,
        max_conversations: int = 3,
        max_decisions: int = 5,
        time_window_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Retrieve comprehensive cross-session context for a user query
        """
        try:
            context_start_time = datetime.now(timezone.utc)
            cutoff_date = context_start_time - timedelta(days=time_window_days)

            # 1. Get relevant memories through semantic search
            relevant_memories = await self._get_relevant_memories(
                user_id, query, max_memories, cutoff_date
            )

            # 2. Get recent conversations with context scoring
            relevant_conversations = await self._get_relevant_conversations(
                db, user_id, query, session_id, max_conversations, cutoff_date
            )

            # 3. Get related decisions
            relevant_decisions = await self._get_relevant_decisions(
                db, user_id, query, max_decisions, cutoff_date
            )

            # 4. Calculate overall relevance scores
            scored_context = await self._calculate_relevance_scores(
                relevant_memories, relevant_conversations, relevant_decisions, query
            )

            # 5. Aggregate and summarize context
            aggregated_context = await self._aggregate_context(
                scored_context, query, user_id
            )

            context_end_time = datetime.now(timezone.utc)
            retrieval_time = (context_end_time - context_start_time).total_seconds()

            result = {
                "user_id": user_id,
                "query": query,
                "session_id": session_id,
                "context": aggregated_context,
                "metadata": {
                    "memories_found": len(relevant_memories),
                    "conversations_found": len(relevant_conversations),
                    "decisions_found": len(relevant_decisions),
                    "retrieval_time_seconds": retrieval_time,
                    "time_window_days": time_window_days,
                    "retrieved_at": context_end_time.isoformat(),
                },
            }

            logger.info(
                f"Retrieved cross-session context for user {user_id}: {len(relevant_memories)} memories, {len(relevant_conversations)} conversations"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to get cross-session context: {e}")
            raise

    async def _get_relevant_memories(
        self, user_id: str, query: str, max_items: int, cutoff_date: datetime
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant memories using semantic search"""
        try:
            # Search for semantically similar memories
            memories = await self.memory_service.search_memories(
                query=query,
                user_id=user_id,
                limit=max_items * 2,  # Get more to allow for filtering
                min_similarity=0.6,
            )

            # Filter by date and active status, then limit
            filtered_memories = []
            for memory in memories:
                memory_date = datetime.fromisoformat(
                    memory["created_at"].replace("Z", "+00:00")
                )
                if memory_date >= cutoff_date:
                    filtered_memories.append(memory)

                if len(filtered_memories) >= max_items:
                    break

            return filtered_memories

        except Exception as e:
            logger.error(f"Failed to get relevant memories: {e}")
            return []

    async def _get_relevant_conversations(
        self,
        db: Session,
        user_id: str,
        query: str,
        current_session_id: Optional[str],
        max_items: int,
        cutoff_date: datetime,
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant conversations with basic relevance scoring"""
        try:
            # Get recent conversations excluding current session
            conversation_query = db.query(Conversation).filter(
                Conversation.user_id == user_id,
                Conversation.created_at >= cutoff_date,
                Conversation.is_archived == False,
            )

            if current_session_id:
                conversation_query = conversation_query.filter(
                    Conversation.session_id != current_session_id
                )

            conversations = (
                conversation_query.order_by(desc(Conversation.last_activity_at))
                .limit(max_items * 2)
                .all()
            )

            # Score conversations based on title and content relevance
            scored_conversations = []
            query_keywords = set(query.lower().split())

            for conv in conversations:
                relevance_score = self._calculate_text_relevance(
                    conv.title, query_keywords
                )

                # Get a sample of conversation messages for context
                sample_messages = (
                    db.query(ConversationMessage)
                    .filter(ConversationMessage.conversation_id == conv.id)
                    .order_by(ConversationMessage.sequence_number)
                    .limit(3)
                    .all()
                )

                conversation_context = {
                    "id": conv.id,
                    "title": conv.title,
                    "context_type": conv.context_type,
                    "last_activity": conv.last_activity_at.isoformat(),
                    "relevance_score": relevance_score,
                    "sample_messages": [
                        {
                            "type": msg.message_type,
                            "content": (
                                msg.content[:200] + "..."
                                if len(msg.content) > 200
                                else msg.content
                            ),
                            "sequence": msg.sequence_number,
                        }
                        for msg in sample_messages
                    ],
                }

                scored_conversations.append(conversation_context)

            # Sort by relevance score and return top items
            scored_conversations.sort(key=lambda x: x["relevance_score"], reverse=True)
            return scored_conversations[:max_items]

        except Exception as e:
            logger.error(f"Failed to get relevant conversations: {e}")
            return []

    async def _get_relevant_decisions(
        self,
        db: Session,
        user_id: str,
        query: str,
        max_items: int,
        cutoff_date: datetime,
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant decisions with basic relevance scoring"""
        try:
            # Get recent decisions
            decisions = (
                db.query(Decision)
                .filter(Decision.user_id == user_id, Decision.decided_at >= cutoff_date)
                .order_by(desc(Decision.decided_at))
                .limit(max_items * 2)
                .all()
            )

            # Score decisions based on title and description relevance
            scored_decisions = []
            query_keywords = set(query.lower().split())

            for decision in decisions:
                title_relevance = self._calculate_text_relevance(
                    decision.title, query_keywords
                )
                desc_relevance = self._calculate_text_relevance(
                    decision.description, query_keywords
                )

                relevance_score = max(title_relevance, desc_relevance * 0.8)

                decision_context = {
                    "id": decision.id,
                    "title": decision.title,
                    "description": (
                        decision.description[:300] + "..."
                        if len(decision.description) > 300
                        else decision.description
                    ),
                    "decision_type": decision.decision_type,
                    "status": decision.status,
                    "priority_level": decision.priority_level,
                    "decided_at": decision.decided_at.isoformat(),
                    "relevance_score": relevance_score,
                }

                scored_decisions.append(decision_context)

            # Sort by relevance score and return top items
            scored_decisions.sort(key=lambda x: x["relevance_score"], reverse=True)
            return scored_decisions[:max_items]

        except Exception as e:
            logger.error(f"Failed to get relevant decisions: {e}")
            return []

    def _calculate_text_relevance(self, text: str, query_keywords: set) -> float:
        """Calculate basic text relevance score based on keyword overlap"""
        if not text or not query_keywords:
            return 0.0

        text_words = set(text.lower().split())
        overlap = query_keywords.intersection(text_words)

        if not overlap:
            return 0.0

        # Calculate relevance based on overlap ratio and word frequency
        overlap_ratio = len(overlap) / len(query_keywords)
        coverage_ratio = len(overlap) / len(text_words) if text_words else 0

        # Weighted combination
        relevance_score = (overlap_ratio * 0.7) + (coverage_ratio * 0.3)

        return min(relevance_score, 1.0)

    async def _calculate_relevance_scores(
        self,
        memories: List[Dict[str, Any]],
        conversations: List[Dict[str, Any]],
        decisions: List[Dict[str, Any]],
        query: str,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Calculate and normalize relevance scores across all context types"""
        try:
            # Memories already have similarity scores from vector search
            for memory in memories:
                # Boost score based on importance and recency
                importance_boost = memory.get("importance_score", 0.5) * 0.2

                # Calculate recency boost (more recent = higher score)
                created_at = datetime.fromisoformat(
                    memory["created_at"].replace("Z", "+00:00")
                )
                days_old = (datetime.now(timezone.utc) - created_at).days
                recency_boost = max(0, (30 - days_old) / 30) * 0.1

                original_score = memory.get("similarity_score", 0.7)
                memory["final_relevance_score"] = min(
                    original_score + importance_boost + recency_boost, 1.0
                )

            # Conversations and decisions already have relevance scores from text matching
            # Add temporal and importance boosts
            for conv in conversations:
                last_activity = datetime.fromisoformat(conv["last_activity"])
                days_old = (datetime.now(timezone.utc) - last_activity).days
                recency_boost = max(0, (7 - days_old) / 7) * 0.2

                conv["final_relevance_score"] = min(
                    conv["relevance_score"] + recency_boost, 1.0
                )

            for decision in decisions:
                decided_at = datetime.fromisoformat(decision["decided_at"])
                days_old = (datetime.now(timezone.utc) - decided_at).days
                recency_boost = max(0, (14 - days_old) / 14) * 0.15

                # Priority boost
                priority_boost = {
                    "critical": 0.2,
                    "high": 0.1,
                    "medium": 0.05,
                    "low": 0.0,
                }.get(decision["priority_level"], 0.0)

                decision["final_relevance_score"] = min(
                    decision["relevance_score"] + recency_boost + priority_boost, 1.0
                )

            return {
                "memories": memories,
                "conversations": conversations,
                "decisions": decisions,
            }

        except Exception as e:
            logger.error(f"Failed to calculate relevance scores: {e}")
            return {
                "memories": memories,
                "conversations": conversations,
                "decisions": decisions,
            }

    async def _aggregate_context(
        self, scored_context: Dict[str, List[Dict[str, Any]]], query: str, user_id: str
    ) -> Dict[str, Any]:
        """Aggregate and summarize context for presentation"""
        try:
            # Sort all items by final relevance score
            all_memories = sorted(
                scored_context["memories"],
                key=lambda x: x.get("final_relevance_score", 0),
                reverse=True,
            )[
                :5
            ]  # Top 5 memories

            all_conversations = sorted(
                scored_context["conversations"],
                key=lambda x: x.get("final_relevance_score", 0),
                reverse=True,
            )[
                :3
            ]  # Top 3 conversations

            all_decisions = sorted(
                scored_context["decisions"],
                key=lambda x: x.get("final_relevance_score", 0),
                reverse=True,
            )[
                :3
            ]  # Top 3 decisions

            # Generate context summary
            context_summary = await self._generate_context_summary(
                all_memories, all_conversations, all_decisions, query
            )

            # Calculate context confidence
            memory_scores = [m.get("final_relevance_score", 0) for m in all_memories]
            conv_scores = [c.get("final_relevance_score", 0) for c in all_conversations]
            decision_scores = [d.get("final_relevance_score", 0) for d in all_decisions]

            all_scores = memory_scores + conv_scores + decision_scores
            context_confidence = (
                sum(all_scores) / len(all_scores) if all_scores else 0.0
            )

            aggregated = {
                "summary": context_summary,
                "context_confidence": context_confidence,
                "relevant_memories": all_memories,
                "relevant_conversations": all_conversations,
                "relevant_decisions": all_decisions,
                "context_categories": self._categorize_context(
                    all_memories, all_conversations, all_decisions
                ),
                "suggested_follow_ups": self._generate_follow_up_suggestions(
                    all_memories, all_conversations, all_decisions, query
                ),
            }

            return aggregated

        except Exception as e:
            logger.error(f"Failed to aggregate context: {e}")
            return {
                "summary": "Error aggregating context",
                "context_confidence": 0.0,
                "relevant_memories": [],
                "relevant_conversations": [],
                "relevant_decisions": [],
            }

    async def _generate_context_summary(
        self,
        memories: List[Dict[str, Any]],
        conversations: List[Dict[str, Any]],
        decisions: List[Dict[str, Any]],
        query: str,
    ) -> str:
        """Generate a concise summary of the retrieved context"""
        try:
            summary_parts = []

            if memories:
                memory_categories = set()
                for memory in memories[:3]:  # Top 3 memories
                    memory_categories.add(memory.get("category", "general"))

                if memory_categories:
                    summary_parts.append(
                        f"Found relevant memories in areas: {', '.join(memory_categories)}"
                    )

            if conversations:
                conv_types = set()
                for conv in conversations:
                    conv_types.add(conv.get("context_type", "general"))

                if conv_types:
                    summary_parts.append(
                        f"Recent conversations about: {', '.join(conv_types)}"
                    )

            if decisions:
                decision_types = set()
                for decision in decisions:
                    decision_types.add(decision.get("decision_type", "general"))

                if decision_types:
                    summary_parts.append(
                        f"Related decisions in: {', '.join(decision_types)}"
                    )

            if summary_parts:
                return ". ".join(summary_parts) + "."
            else:
                return "No significant historical context found for this query."

        except Exception as e:
            logger.error(f"Failed to generate context summary: {e}")
            return "Context summary unavailable."

    def _categorize_context(
        self,
        memories: List[Dict[str, Any]],
        conversations: List[Dict[str, Any]],
        decisions: List[Dict[str, Any]],
    ) -> Dict[str, int]:
        """Categorize context items for better organization"""
        categories = {}

        # Count memory categories
        for memory in memories:
            category = memory.get("category", "unknown")
            categories[f"memory_{category}"] = (
                categories.get(f"memory_{category}", 0) + 1
            )

        # Count conversation types
        for conv in conversations:
            context_type = conv.get("context_type", "unknown")
            categories[f"conversation_{context_type}"] = (
                categories.get(f"conversation_{context_type}", 0) + 1
            )

        # Count decision types
        for decision in decisions:
            decision_type = decision.get("decision_type", "unknown")
            categories[f"decision_{decision_type}"] = (
                categories.get(f"decision_{decision_type}", 0) + 1
            )

        return categories

    def _generate_follow_up_suggestions(
        self,
        memories: List[Dict[str, Any]],
        conversations: List[Dict[str, Any]],
        decisions: List[Dict[str, Any]],
        query: str,
    ) -> List[str]:
        """Generate follow-up suggestions based on context"""
        suggestions = []

        # Suggest based on incomplete decisions
        pending_decisions = [d for d in decisions if d.get("status") == "pending"]
        if pending_decisions:
            suggestions.append("Review pending decisions that may be related")

        # Suggest based on conversation patterns
        unresolved_conversations = [
            c for c in conversations if c.get("context_type") == "ad_hoc_query"
        ]
        if unresolved_conversations:
            suggestions.append("Check if previous similar queries were resolved")

        # Suggest based on memory patterns
        preference_memories = [m for m in memories if m.get("category") == "preference"]
        if preference_memories:
            suggestions.append("Consider user preferences from past interactions")

        # Generic suggestions if none specific
        if not suggestions:
            suggestions = [
                "Explore related team discussions",
                "Review recent project updates",
                "Check for similar past queries",
            ]

        return suggestions[:3]  # Return top 3 suggestions

    async def get_contextual_memory_search(
        self,
        db: Session,
        user_id: str,
        query: str,
        context_filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Enhanced memory search with contextual filtering"""
        try:
            # Default context filters
            filters = context_filters or {}

            # Get base semantic search results
            base_results = await self.memory_service.search_memories(
                query=query,
                user_id=user_id,
                memory_types=filters.get("memory_types"),
                categories=filters.get("categories"),
                limit=limit * 2,  # Get more for filtering
                min_similarity=filters.get("min_similarity", 0.6),
            )

            # Apply additional contextual filters
            filtered_results = []
            for result in base_results:
                # Apply importance filter
                if (
                    filters.get("min_importance")
                    and result.get("importance_score", 0) < filters["min_importance"]
                ):
                    continue

                # Apply recency filter
                if filters.get("max_age_days"):
                    created_at = datetime.fromisoformat(
                        result["created_at"].replace("Z", "+00:00")
                    )
                    days_old = (datetime.now(timezone.utc) - created_at).days
                    if days_old > filters["max_age_days"]:
                        continue

                filtered_results.append(result)

            # Limit results
            final_results = filtered_results[:limit]

            return {
                "query": query,
                "user_id": user_id,
                "filters_applied": filters,
                "results": final_results,
                "total_found": len(filtered_results),
                "total_returned": len(final_results),
                "searched_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed contextual memory search: {e}")
            raise

# Global context retrieval service instance
context_retrieval_service = ContextRetrievalService()
