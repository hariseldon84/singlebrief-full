"""
Tests for Memory System including vector database integration
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from app.ai.vector_database import (
    EmbeddingGenerator, 
    WeaviateVectorDatabase, 
    PineconeVectorDatabase,
    VectorDatabaseManager
)
from app.ai.memory_service import MemoryService
from app.models.memory import UserMemory, TeamMemory


class TestEmbeddingGenerator:
    """Test embedding generation functionality"""

    @pytest.fixture
    def embedding_generator(self):
        return EmbeddingGenerator()

    def test_get_content_hash(self, embedding_generator):
        """Test content hash generation"""
        content = "This is test content"
        hash1 = embedding_generator.get_content_hash(content)
        hash2 = embedding_generator.get_content_hash(content)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
        
        # Different content should produce different hash
        different_hash = embedding_generator.get_content_hash("Different content")
        assert hash1 != different_hash

    @patch('openai.OpenAI')
    async def test_generate_embedding(self, mock_openai, embedding_generator):
        """Test embedding generation with mocked OpenAI"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
        mock_openai.return_value.embeddings.create.return_value = mock_response
        
        # Mock settings
        with patch('app.ai.vector_database.settings.OPENAI_API_KEY', 'test-key'):
            embedding = await embedding_generator.generate_embedding("test content")
        
        assert embedding == [0.1, 0.2, 0.3]
        mock_openai.return_value.embeddings.create.assert_called_once()

    async def test_generate_embedding_no_api_key(self, embedding_generator):
        """Test embedding generation fails without API key"""
        with patch('app.ai.vector_database.settings.OPENAI_API_KEY', None):
            with pytest.raises(ValueError, match="OpenAI API key not configured"):
                await embedding_generator.generate_embedding("test content")


class TestWeaviateVectorDatabase:
    """Test Weaviate vector database operations"""

    @pytest.fixture
    def weaviate_db(self):
        return WeaviateVectorDatabase()

    @patch('weaviate.Client')
    async def test_initialize(self, mock_weaviate_client, weaviate_db):
        """Test Weaviate initialization"""
        mock_client = Mock()
        mock_client.schema.contains.return_value = True
        mock_weaviate_client.return_value = mock_client
        
        with patch('app.ai.vector_database.settings.WEAVIATE_URL', 'http://localhost:8080'):
            result = await weaviate_db.initialize()
        
        assert result is True
        assert weaviate_db.client is not None

    async def test_create_memory_embedding(self, weaviate_db):
        """Test creating memory embedding in Weaviate"""
        # Mock client and embedding generator
        mock_client = Mock()
        mock_client.data_object.create.return_value = "test-vector-id"
        weaviate_db.client = mock_client
        
        with patch.object(weaviate_db.embedding_generator, 'generate_embedding', 
                         new_callable=AsyncMock, return_value=[0.1, 0.2, 0.3]):
            
            vector_id = await weaviate_db.create_memory_embedding(
                content="test content",
                memory_id="test-memory-id",
                memory_type="user_memory",
                metadata={
                    "user_id": "test-user",
                    "organization_id": "test-org",
                    "category": "test-category",
                    "importance_score": 0.8
                }
            )
        
        assert vector_id == "test-vector-id"
        mock_client.data_object.create.assert_called_once()

    async def test_search_similar_memories(self, weaviate_db):
        """Test searching similar memories in Weaviate"""
        # Mock client and search results
        mock_client = Mock()
        mock_search_result = {
            "data": {
                "Get": {
                    "MemoryEmbedding": [
                        {
                            "memoryId": "memory-1",
                            "memoryType": "user_memory",
                            "userId": "user-1",
                            "content": "test content",
                            "category": "test",
                            "importanceScore": 0.8,
                            "createdAt": "2024-01-01T00:00:00Z",
                            "_additional": {
                                "certainty": 0.9,
                                "distance": 0.1
                            }
                        }
                    ]
                }
            }
        }
        
        mock_query = Mock()
        mock_query.get.return_value = mock_query
        mock_query.with_near_vector.return_value = mock_query
        mock_query.with_limit.return_value = mock_query
        mock_query.with_additional.return_value = mock_query
        mock_query.do.return_value = mock_search_result
        
        mock_client.query = mock_query
        weaviate_db.client = mock_client
        
        with patch.object(weaviate_db.embedding_generator, 'generate_embedding',
                         new_callable=AsyncMock, return_value=[0.1, 0.2, 0.3]):
            
            results = await weaviate_db.search_similar_memories(
                query="test query",
                user_id="user-1",
                limit=5,
                min_similarity=0.7
            )
        
        assert len(results) == 1
        assert results[0]["memory_id"] == "memory-1"
        assert results[0]["similarity_score"] == 0.9


class TestPineconeVectorDatabase:
    """Test Pinecone vector database operations"""

    @pytest.fixture
    def pinecone_db(self):
        return PineconeVectorDatabase()

    @patch('pinecone.init')
    @patch('pinecone.list_indexes')
    @patch('pinecone.Index')
    async def test_initialize(self, mock_index, mock_list_indexes, mock_init, pinecone_db):
        """Test Pinecone initialization"""
        mock_list_indexes.return_value = ["singlebrief-memories"]
        mock_index_instance = Mock()
        mock_index.return_value = mock_index_instance
        
        with patch('app.ai.vector_database.settings.PINECONE_API_KEY', 'test-key'), \
             patch('app.ai.vector_database.settings.PINECONE_ENVIRONMENT', 'test-env'):
            
            result = await pinecone_db.initialize()
        
        assert result is True
        assert pinecone_db.index is not None
        mock_init.assert_called_once()

    async def test_create_memory_embedding(self, pinecone_db):
        """Test creating memory embedding in Pinecone"""
        mock_index = Mock()
        pinecone_db.index = mock_index
        
        with patch.object(pinecone_db.embedding_generator, 'generate_embedding',
                         new_callable=AsyncMock, return_value=[0.1, 0.2, 0.3]):
            
            vector_id = await pinecone_db.create_memory_embedding(
                content="test content",
                memory_id="test-memory-id",
                memory_type="user_memory",
                metadata={
                    "user_id": "test-user",
                    "organization_id": "test-org",
                    "category": "test-category",
                    "importance_score": 0.8
                }
            )
        
        assert vector_id == "user_memory_test-memory-id"
        mock_index.upsert.assert_called_once()

    async def test_search_similar_memories(self, pinecone_db):
        """Test searching similar memories in Pinecone"""
        mock_index = Mock()
        mock_match = Mock()
        mock_match.id = "user_memory_memory-1"
        mock_match.score = 0.9
        mock_match.metadata = {
            "memory_id": "memory-1",
            "memory_type": "user_memory",
            "user_id": "user-1",
            "content": "test content",
            "category": "test",
            "importance_score": 0.8,
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        mock_query_result = Mock()
        mock_query_result.matches = [mock_match]
        mock_index.query.return_value = mock_query_result
        
        pinecone_db.index = mock_index
        
        with patch.object(pinecone_db.embedding_generator, 'generate_embedding',
                         new_callable=AsyncMock, return_value=[0.1, 0.2, 0.3]):
            
            results = await pinecone_db.search_similar_memories(
                query="test query",
                user_id="user-1",
                limit=5,
                min_similarity=0.7
            )
        
        assert len(results) == 1
        assert results[0]["memory_id"] == "memory-1"
        assert results[0]["similarity_score"] == 0.9


class TestVectorDatabaseManager:
    """Test vector database manager functionality"""

    def test_weaviate_initialization(self):
        """Test manager with Weaviate"""
        manager = VectorDatabaseManager(database_type="weaviate")
        assert isinstance(manager.db, WeaviateVectorDatabase)

    def test_pinecone_initialization(self):
        """Test manager with Pinecone"""
        manager = VectorDatabaseManager(database_type="pinecone")
        assert isinstance(manager.db, PineconeVectorDatabase)

    def test_invalid_database_type(self):
        """Test manager with invalid database type"""
        with pytest.raises(ValueError, match="Unsupported database type"):
            VectorDatabaseManager(database_type="invalid")

    async def test_create_memory_embedding_user_memory(self):
        """Test creating embedding for user memory"""
        manager = VectorDatabaseManager(database_type="weaviate")
        
        # Mock the database
        mock_db = Mock()
        mock_db.create_memory_embedding = AsyncMock(return_value="test-vector-id")
        manager.db = mock_db
        
        # Create test user memory
        user_memory = UserMemory(
            id="test-memory-id",
            user_id="test-user",
            organization_id="test-org",
            memory_type="preference",
            category="communication",
            content="User prefers brief updates",
            importance_score=0.8
        )
        
        vector_id = await manager.create_memory_embedding(user_memory)
        
        assert vector_id == "test-vector-id"
        mock_db.create_memory_embedding.assert_called_once()

    async def test_create_memory_embedding_team_memory(self):
        """Test creating embedding for team memory"""
        manager = VectorDatabaseManager(database_type="weaviate")
        
        # Mock the database
        mock_db = Mock()
        mock_db.create_memory_embedding = AsyncMock(return_value="test-vector-id")
        manager.db = mock_db
        
        # Create test team memory
        team_memory = TeamMemory(
            id="test-memory-id",
            team_id="test-team",
            organization_id="test-org",
            created_by_user_id="test-user",
            memory_type="team_process",
            category="workflow",
            title="Sprint Planning Process",
            content="Team conducts sprint planning every Monday",
            importance_score=0.9
        )
        
        vector_id = await manager.create_memory_embedding(team_memory)
        
        assert vector_id == "test-vector-id"
        mock_db.create_memory_embedding.assert_called_once()


class TestMemoryService:
    """Test memory service functionality"""

    @pytest.fixture
    def memory_service(self):
        service = MemoryService()
        # Mock the vector database
        service.vector_db = Mock()
        service.vector_db.initialize = AsyncMock(return_value=True)
        service.vector_db.create_memory_embedding = AsyncMock(return_value="test-vector-id")
        service.vector_db.database_type = "weaviate"
        service.vector_db.db = Mock()
        service.vector_db.db.embedding_generator = Mock()
        service.vector_db.db.embedding_generator.get_content_hash = Mock(return_value="test-hash")
        return service

    async def test_initialize(self, memory_service):
        """Test memory service initialization"""
        result = await memory_service.initialize()
        assert result is True
        memory_service.vector_db.initialize.assert_called_once()

    async def test_search_memories(self, memory_service):
        """Test memory search functionality"""
        # Mock search results
        mock_results = [
            {
                "memory_id": "memory-1",
                "memory_type": "user_memory",
                "category": "preference",
                "content": "Test memory",
                "similarity_score": 0.9
            }
        ]
        memory_service.vector_db.search_similar_memories = AsyncMock(return_value=mock_results)
        
        results = await memory_service.search_memories(
            query="test query",
            user_id="test-user",
            memory_types=["user_memory"],
            categories=["preference"]
        )
        
        assert len(results) == 1
        assert results[0]["memory_id"] == "memory-1"
        memory_service.vector_db.search_similar_memories.assert_called_once()

    async def test_search_memories_with_filters(self, memory_service):
        """Test memory search with type and category filters"""
        # Mock search results with different types
        mock_results = [
            {
                "memory_id": "memory-1",
                "memory_type": "user_memory",
                "category": "preference",
                "similarity_score": 0.9
            },
            {
                "memory_id": "memory-2", 
                "memory_type": "team_memory",
                "category": "process",
                "similarity_score": 0.8
            }
        ]
        memory_service.vector_db.search_similar_memories = AsyncMock(return_value=mock_results)
        
        # Filter for only user memories with preference category
        results = await memory_service.search_memories(
            query="test query",
            memory_types=["user_memory"],
            categories=["preference"]
        )
        
        assert len(results) == 1
        assert results[0]["memory_id"] == "memory-1"


# Integration test markers
pytestmark = pytest.mark.asyncio