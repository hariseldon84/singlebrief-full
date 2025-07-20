"""
Vector Database Integration for Memory Engine
Supports both Weaviate and Pinecone for semantic memory search
"""

from typing import Any, Dict, List, Optional, Tuple

import hashlib
import logging
from abc import ABC, abstractmethod
from datetime import datetime

import openai
import pinecone
import weaviate

from app.core.config import settings
from app.models.memory import MemoryEmbedding, TeamMemory, UserMemory

logger = logging.getLogger(__name__)

class VectorDatabaseInterface(ABC):
    """Abstract interface for vector database operations"""

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the vector database connection"""
        pass

    @abstractmethod
    async def create_memory_embedding(
        self, content: str, memory_id: str, memory_type: str, metadata: Dict[str, Any]
    ) -> str:
        """Create and store a memory embedding"""
        pass

    @abstractmethod
    async def search_similar_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        team_id: Optional[str] = None,
        limit: int = 10,
        min_similarity: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """Search for similar memories"""
        pass

    @abstractmethod
    async def delete_memory_embedding(self, vector_id: str) -> bool:
        """Delete a memory embedding"""
        pass

    @abstractmethod
    async def update_memory_embedding(
        self, vector_id: str, content: str, metadata: Dict[str, Any]
    ) -> bool:
        """Update an existing memory embedding"""
        pass

class EmbeddingGenerator:
    """Generates vector embeddings using OpenAI's embedding models"""

    def __init__(self, model: str = "text-embedding-ada-002"):
        self.model = model
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for given text"""
        try:
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API key not configured")

            response = self.client.embeddings.create(model=self.model, input=text)
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    def get_content_hash(self, content: str) -> str:
        """Generate hash for content change detection"""
        return hashlib.sha256(content.encode()).hexdigest()

class WeaviateVectorDatabase(VectorDatabaseInterface):
    """Weaviate implementation for vector memory storage"""

    def __init__(self):
        self.client = None
        self.embedding_generator = EmbeddingGenerator()
        self.class_name = "MemoryEmbedding"

    async def initialize(self) -> bool:
        """Initialize Weaviate connection and schema"""
        try:
            auth_config = None
            if settings.WEAVIATE_API_KEY:
                auth_config = weaviate.AuthApiKey(api_key=settings.WEAVIATE_API_KEY)

            self.client = weaviate.Client(
                url=settings.WEAVIATE_URL, auth_client_secret=auth_config
            )

            # Create schema if it doesn't exist
            await self._create_schema()
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Weaviate: {e}")
            return False

    async def _create_schema(self):
        """Create Weaviate schema for memory embeddings"""
        schema = {
            "class": self.class_name,
            "description": "Memory embeddings for SingleBrief AI system",
            "properties": [
                {
                    "name": "memoryId",
                    "dataType": ["string"],
                    "description": "ID of the associated memory record",
                },
                {
                    "name": "memoryType",
                    "dataType": ["string"],
                    "description": "Type of memory: user_memory or team_memory",
                },
                {
                    "name": "userId",
                    "dataType": ["string"],
                    "description": "ID of the user (for user memories)",
                },
                {
                    "name": "teamId",
                    "dataType": ["string"],
                    "description": "ID of the team (for team memories)",
                },
                {
                    "name": "organizationId",
                    "dataType": ["string"],
                    "description": "ID of the organization",
                },
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Original content that was embedded",
                },
                {
                    "name": "category",
                    "dataType": ["string"],
                    "description": "Memory category for filtering",
                },
                {
                    "name": "importanceScore",
                    "dataType": ["number"],
                    "description": "Importance score for ranking",
                },
                {
                    "name": "createdAt",
                    "dataType": ["date"],
                    "description": "Creation timestamp",
                },
            ],
            "vectorizer": "none",  # We'll provide our own vectors
        }

        try:
            if not self.client.schema.contains({"class": self.class_name}):
                self.client.schema.create_class(schema)
                logger.info(f"Created Weaviate class: {self.class_name}")
        except Exception as e:
            logger.error(f"Failed to create Weaviate schema: {e}")
            raise

    async def create_memory_embedding(
        self, content: str, memory_id: str, memory_type: str, metadata: Dict[str, Any]
    ) -> str:
        """Create and store a memory embedding in Weaviate"""
        try:
            # Generate embedding
            embedding = await self.embedding_generator.generate_embedding(content)

            # Prepare object data
            data_object = {
                "memoryId": memory_id,
                "memoryType": memory_type,
                "userId": metadata.get("user_id"),
                "teamId": metadata.get("team_id"),
                "organizationId": metadata.get("organization_id"),
                "content": content,
                "category": metadata.get("category"),
                "importanceScore": metadata.get("importance_score", 0.5),
                "createdAt": datetime.utcnow().isoformat(),
            }

            # Store in Weaviate
            result = self.client.data_object.create(
                data_object=data_object, class_name=self.class_name, vector=embedding
            )

            logger.info(f"Created Weaviate embedding for memory {memory_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to create Weaviate embedding: {e}")
            raise

    async def search_similar_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        team_id: Optional[str] = None,
        limit: int = 10,
        min_similarity: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """Search for similar memories in Weaviate"""
        try:
            # Generate query embedding
            query_embedding = await self.embedding_generator.generate_embedding(query)

            # Build where filter
            where_filter = {"operator": "And", "operands": []}

            if user_id:
                where_filter["operands"].append(
                    {"path": ["userId"], "operator": "Equal", "valueString": user_id}
                )

            if team_id:
                where_filter["operands"].append(
                    {"path": ["teamId"], "operator": "Equal", "valueString": team_id}
                )

            # Execute search
            result = (
                self.client.query.get(
                    self.class_name,
                    [
                        "memoryId",
                        "memoryType",
                        "userId",
                        "teamId",
                        "content",
                        "category",
                        "importanceScore",
                        "createdAt",
                    ],
                )
                .with_near_vector(
                    {"vector": query_embedding, "certainty": min_similarity}
                )
                .with_limit(limit)
                .with_additional(["certainty", "distance"])
            )

            if where_filter["operands"]:
                result = result.with_where(where_filter)

            search_results = result.do()

            # Process results
            memories = []
            if "data" in search_results and "Get" in search_results["data"]:
                for item in search_results["data"]["Get"][self.class_name]:
                    memories.append(
                        {
                            "memory_id": item["memoryId"],
                            "memory_type": item["memoryType"],
                            "user_id": item.get("userId"),
                            "team_id": item.get("teamId"),
                            "content": item["content"],
                            "category": item["category"],
                            "importance_score": item["importanceScore"],
                            "similarity_score": item["_additional"]["certainty"],
                            "distance": item["_additional"]["distance"],
                            "created_at": item["createdAt"],
                        }
                    )

            logger.info(f"Found {len(memories)} similar memories for query")
            return memories

        except Exception as e:
            logger.error(f"Failed to search Weaviate memories: {e}")
            raise

    async def delete_memory_embedding(self, vector_id: str) -> bool:
        """Delete a memory embedding from Weaviate"""
        try:
            self.client.data_object.delete(vector_id)
            logger.info(f"Deleted Weaviate embedding {vector_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete Weaviate embedding {vector_id}: {e}")
            return False

    async def update_memory_embedding(
        self, vector_id: str, content: str, metadata: Dict[str, Any]
    ) -> bool:
        """Update an existing memory embedding in Weaviate"""
        try:
            # Generate new embedding
            embedding = await self.embedding_generator.generate_embedding(content)

            # Update object
            data_object = {
                "content": content,
                "category": metadata.get("category"),
                "importanceScore": metadata.get("importance_score", 0.5),
            }

            self.client.data_object.update(
                data_object=data_object,
                class_name=self.class_name,
                uuid=vector_id,
                vector=embedding,
            )

            logger.info(f"Updated Weaviate embedding {vector_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update Weaviate embedding {vector_id}: {e}")
            return False

class PineconeVectorDatabase(VectorDatabaseInterface):
    """Pinecone implementation for vector memory storage"""

    def __init__(self):
        self.index = None
        self.embedding_generator = EmbeddingGenerator()
        self.index_name = "singlebrief-memories"

    async def initialize(self) -> bool:
        """Initialize Pinecone connection and index"""
        try:
            pinecone.init(
                api_key=settings.PINECONE_API_KEY,
                environment=settings.PINECONE_ENVIRONMENT,
            )

            # Create index if it doesn't exist
            if self.index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=self.index_name,
                    dimension=1536,  # OpenAI embedding dimension
                    metric="cosine",
                )

            self.index = pinecone.Index(self.index_name)
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            return False

    async def create_memory_embedding(
        self, content: str, memory_id: str, memory_type: str, metadata: Dict[str, Any]
    ) -> str:
        """Create and store a memory embedding in Pinecone"""
        try:
            # Generate embedding
            embedding = await self.embedding_generator.generate_embedding(content)

            # Create vector ID
            vector_id = f"{memory_type}_{memory_id}"

            # Prepare metadata
            vector_metadata = {
                "memory_id": memory_id,
                "memory_type": memory_type,
                "user_id": metadata.get("user_id"),
                "team_id": metadata.get("team_id"),
                "organization_id": metadata.get("organization_id"),
                "content": content[:1000],  # Pinecone has metadata size limits
                "category": metadata.get("category"),
                "importance_score": metadata.get("importance_score", 0.5),
                "created_at": datetime.utcnow().isoformat(),
            }

            # Store in Pinecone
            self.index.upsert([(vector_id, embedding, vector_metadata)])

            logger.info(f"Created Pinecone embedding for memory {memory_id}")
            return vector_id

        except Exception as e:
            logger.error(f"Failed to create Pinecone embedding: {e}")
            raise

    async def search_similar_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        team_id: Optional[str] = None,
        limit: int = 10,
        min_similarity: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """Search for similar memories in Pinecone"""
        try:
            # Generate query embedding
            query_embedding = await self.embedding_generator.generate_embedding(query)

            # Build filter
            filter_dict = {}
            if user_id:
                filter_dict["user_id"] = {"$eq": user_id}
            if team_id:
                filter_dict["team_id"] = {"$eq": team_id}

            # Execute search
            search_results = self.index.query(
                vector=query_embedding,
                top_k=limit,
                include_metadata=True,
                filter=filter_dict if filter_dict else None,
            )

            # Process results
            memories = []
            for match in search_results.matches:
                if match.score >= min_similarity:
                    memories.append(
                        {
                            "vector_id": match.id,
                            "memory_id": match.metadata["memory_id"],
                            "memory_type": match.metadata["memory_type"],
                            "user_id": match.metadata.get("user_id"),
                            "team_id": match.metadata.get("team_id"),
                            "content": match.metadata["content"],
                            "category": match.metadata["category"],
                            "importance_score": match.metadata["importance_score"],
                            "similarity_score": match.score,
                            "created_at": match.metadata["created_at"],
                        }
                    )

            logger.info(f"Found {len(memories)} similar memories for query")
            return memories

        except Exception as e:
            logger.error(f"Failed to search Pinecone memories: {e}")
            raise

    async def delete_memory_embedding(self, vector_id: str) -> bool:
        """Delete a memory embedding from Pinecone"""
        try:
            self.index.delete(ids=[vector_id])
            logger.info(f"Deleted Pinecone embedding {vector_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete Pinecone embedding {vector_id}: {e}")
            return False

    async def update_memory_embedding(
        self, vector_id: str, content: str, metadata: Dict[str, Any]
    ) -> bool:
        """Update an existing memory embedding in Pinecone"""
        try:
            # Generate new embedding
            embedding = await self.embedding_generator.generate_embedding(content)

            # Update metadata
            vector_metadata = {
                "content": content[:1000],
                "category": metadata.get("category"),
                "importance_score": metadata.get("importance_score", 0.5),
            }

            # Upsert (update or insert)
            self.index.upsert([(vector_id, embedding, vector_metadata)])

            logger.info(f"Updated Pinecone embedding {vector_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update Pinecone embedding {vector_id}: {e}")
            return False

class VectorDatabaseManager:
    """Manager class for vector database operations"""

    def __init__(self, database_type: str = "weaviate"):
        self.database_type = database_type
        if database_type == "weaviate":
            self.db = WeaviateVectorDatabase()
        elif database_type == "pinecone":
            self.db = PineconeVectorDatabase()
        else:
            raise ValueError(f"Unsupported database type: {database_type}")

    async def initialize(self) -> bool:
        """Initialize the vector database"""
        return await self.db.initialize()

    async def create_memory_embedding(
        self, memory: UserMemory | TeamMemory
    ) -> Optional[str]:
        """Create embedding for a memory object"""
        try:
            if isinstance(memory, UserMemory):
                memory_type = "user_memory"
                metadata = {
                    "user_id": memory.user_id,
                    "organization_id": memory.organization_id,
                    "category": memory.category,
                    "importance_score": memory.importance_score,
                }
            else:  # TeamMemory
                memory_type = "team_memory"
                metadata = {
                    "team_id": memory.team_id,
                    "organization_id": memory.organization_id,
                    "user_id": memory.created_by_user_id,
                    "category": memory.category,
                    "importance_score": memory.importance_score,
                }

            vector_id = await self.db.create_memory_embedding(
                content=memory.content,
                memory_id=memory.id,
                memory_type=memory_type,
                metadata=metadata,
            )

            return vector_id

        except Exception as e:
            logger.error(f"Failed to create memory embedding: {e}")
            return None

    async def search_similar_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        team_id: Optional[str] = None,
        limit: int = 10,
        min_similarity: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """Search for similar memories"""
        return await self.db.search_similar_memories(
            query=query,
            user_id=user_id,
            team_id=team_id,
            limit=limit,
            min_similarity=min_similarity,
        )

    async def delete_memory_embedding(self, vector_id: str) -> bool:
        """Delete a memory embedding"""
        return await self.db.delete_memory_embedding(vector_id)

    async def update_memory_embedding(
        self, vector_id: str, memory: UserMemory | TeamMemory
    ) -> bool:
        """Update an existing memory embedding"""
        metadata = {
            "category": memory.category,
            "importance_score": memory.importance_score,
        }
        return await self.db.update_memory_embedding(
            vector_id=vector_id, content=memory.content, metadata=metadata
        )

# Global vector database manager instance
vector_db_manager = VectorDatabaseManager(database_type=settings.VECTOR_DATABASE_TYPE)
