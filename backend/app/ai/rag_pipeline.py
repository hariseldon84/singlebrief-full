"""
Retrieval-Augmented Generation (RAG) Pipeline
Advanced context retrieval and augmentation system
"""

import logging
import asyncio
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS, Weaviate
from langchain.text_splitter import RecursiveCharacterTextSplitter, TokenTextSplitter
from langchain.schema import Document
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

from app.core.config import get_settings
from app.ai.llm_integration import LLMManager, QueryType

logger = logging.getLogger(__name__)
settings = get_settings()


class RetrievalType(str, Enum):
    """Types of retrieval strategies"""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    MULTI_QUERY = "multi_query"
    CONTEXTUAL = "contextual"


class DocumentType(str, Enum):
    """Types of documents in the system"""
    TEAM_COMMUNICATION = "team_communication"
    PROJECT_DOCUMENTATION = "project_documentation"
    MEETING_NOTES = "meeting_notes"
    EMAIL_THREAD = "email_thread"
    CODE_REPOSITORY = "code_repository"
    EXTERNAL_KNOWLEDGE = "external_knowledge"


@dataclass
class RetrievedContext:
    """Retrieved context with metadata"""
    content: str
    source: str
    document_type: DocumentType
    relevance_score: float
    chunk_index: int
    metadata: Dict[str, Any]
    retrieved_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RAGResult:
    """Complete RAG result with context and metadata"""
    query: str
    retrieved_contexts: List[RetrievedContext]
    total_chunks_searched: int
    retrieval_time_ms: int
    retrieval_strategy: RetrievalType
    confidence_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocumentProcessor:
    """Advanced document processing for RAG pipeline"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
        self.token_splitter = TokenTextSplitter(
            chunk_size=512,
            chunk_overlap=50
        )
        
    def process_document(
        self,
        content: str,
        document_type: DocumentType,
        metadata: Dict[str, Any]
    ) -> List[Document]:
        """Process document into chunks with metadata"""
        
        # Choose splitter based on document type
        if document_type in [DocumentType.CODE_REPOSITORY, DocumentType.PROJECT_DOCUMENTATION]:
            chunks = self.text_splitter.split_text(content)
        else:
            chunks = self.token_splitter.split_text(content)
        
        documents = []
        for i, chunk in enumerate(chunks):
            doc_metadata = {
                **metadata,
                'document_type': document_type.value,
                'chunk_index': i,
                'chunk_size': len(chunk),
                'processed_at': datetime.now(timezone.utc).isoformat()
            }
            
            documents.append(Document(
                page_content=chunk,
                metadata=doc_metadata
            ))
        
        return documents
    
    def extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content for hybrid search"""
        # Simple keyword extraction - can be enhanced with NLP libraries
        words = content.lower().split()
        
        # Filter out common stop words and short words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        
        # Return unique keywords, sorted by frequency
        from collections import Counter
        keyword_counts = Counter(keywords)
        return [word for word, count in keyword_counts.most_common(20)]


class VectorStore:
    """Advanced vector store management"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY
        ) if settings.OPENAI_API_KEY else None
        
        self.vector_stores = {}
        self.indices = {}
        
        if not self.embeddings:
            logger.warning("No embedding model available - vector search disabled")
    
    async def create_index(
        self,
        index_name: str,
        documents: List[Document],
        index_type: str = "faiss"
    ) -> bool:
        """Create or update vector index"""
        
        if not self.embeddings:
            logger.error("Cannot create index without embeddings")
            return False
        
        try:
            if index_type.lower() == "faiss":
                vector_store = FAISS.from_documents(documents, self.embeddings)
                self.vector_stores[index_name] = vector_store
                
            elif index_type.lower() == "weaviate" and settings.WEAVIATE_URL:
                vector_store = Weaviate.from_documents(
                    documents,
                    self.embeddings,
                    weaviate_url=settings.WEAVIATE_URL,
                    by_text=False
                )
                self.vector_stores[index_name] = vector_store
            
            else:
                logger.error(f"Unsupported index type: {index_type}")
                return False
            
            logger.info(f"Created vector index '{index_name}' with {len(documents)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create vector index: {e}")
            return False
    
    async def similarity_search(
        self,
        index_name: str,
        query: str,
        k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Tuple[Document, float]]:
        """Perform similarity search on vector index"""
        
        if index_name not in self.vector_stores:
            logger.error(f"Index '{index_name}' not found")
            return []
        
        try:
            vector_store = self.vector_stores[index_name]
            results = vector_store.similarity_search_with_score(query, k=k)
            
            # Filter by score threshold
            filtered_results = [(doc, score) for doc, score in results if score >= score_threshold]
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []


class RAGPipeline:
    """
    Advanced Retrieval-Augmented Generation Pipeline.
    
    Features:
    1. Multiple retrieval strategies (semantic, keyword, hybrid)
    2. Document processing and chunking
    3. Vector store management
    4. Context ranking and filtering
    5. Multi-query expansion
    6. Contextual compression
    """
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.vector_store = VectorStore()
        self.llm_manager = LLMManager()
        
        # Document storage by type
        self.document_stores = {doc_type: [] for doc_type in DocumentType}
        
        # Retrieval statistics
        self.retrieval_stats = {
            'total_queries': 0,
            'total_documents_indexed': 0,
            'average_retrieval_time': 0.0,
            'retrieval_methods': {}
        }
        
        logger.info("RAG Pipeline initialized")
    
    async def index_document(
        self,
        content: str,
        document_type: DocumentType,
        metadata: Dict[str, Any]
    ) -> bool:
        """Index a document for retrieval"""
        
        try:
            # Process document into chunks
            documents = self.document_processor.process_document(
                content, document_type, metadata
            )
            
            # Store documents
            self.document_stores[document_type].extend(documents)
            
            # Create/update vector index
            index_name = f"{document_type.value}_index"
            success = await self.vector_store.create_index(index_name, documents)
            
            if success:
                self.retrieval_stats['total_documents_indexed'] += len(documents)
                logger.info(f"Indexed document: {len(documents)} chunks for {document_type.value}")
            
            return success
            
        except Exception as e:
            logger.error(f"Document indexing failed: {e}")
            return False
    
    async def retrieve_context(
        self,
        query: str,
        retrieval_type: RetrievalType = RetrievalType.HYBRID,
        document_types: Optional[List[DocumentType]] = None,
        max_contexts: int = 5,
        score_threshold: float = 0.3
    ) -> RAGResult:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: Search query
            retrieval_type: Strategy to use for retrieval
            document_types: Types of documents to search (None = all)
            max_contexts: Maximum number of contexts to return
            score_threshold: Minimum relevance score threshold
            
        Returns:
            RAGResult with retrieved contexts and metadata
        """
        
        start_time = datetime.now()
        
        try:
            if document_types is None:
                document_types = list(DocumentType)
            
            retrieved_contexts = []
            total_chunks_searched = 0
            
            if retrieval_type == RetrievalType.SEMANTIC:
                contexts = await self._semantic_retrieval(
                    query, document_types, max_contexts, score_threshold
                )
                retrieved_contexts.extend(contexts)
                
            elif retrieval_type == RetrievalType.KEYWORD:
                contexts = await self._keyword_retrieval(
                    query, document_types, max_contexts, score_threshold
                )
                retrieved_contexts.extend(contexts)
                
            elif retrieval_type == RetrievalType.HYBRID:
                # Combine semantic and keyword search
                semantic_contexts = await self._semantic_retrieval(
                    query, document_types, max_contexts // 2, score_threshold
                )
                keyword_contexts = await self._keyword_retrieval(
                    query, document_types, max_contexts // 2, score_threshold
                )
                
                # Merge and deduplicate
                all_contexts = semantic_contexts + keyword_contexts
                retrieved_contexts = self._deduplicate_contexts(all_contexts)[:max_contexts]
                
            elif retrieval_type == RetrievalType.MULTI_QUERY:
                contexts = await self._multi_query_retrieval(
                    query, document_types, max_contexts, score_threshold
                )
                retrieved_contexts.extend(contexts)
                
            elif retrieval_type == RetrievalType.CONTEXTUAL:
                contexts = await self._contextual_retrieval(
                    query, document_types, max_contexts, score_threshold
                )
                retrieved_contexts.extend(contexts)
            
            # Calculate metrics
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            total_chunks_searched = sum(len(self.document_stores[dt]) for dt in document_types)
            
            # Calculate confidence score
            confidence_score = self._calculate_retrieval_confidence(retrieved_contexts)
            
            # Update statistics
            self._update_retrieval_stats(retrieval_type, processing_time)
            
            return RAGResult(
                query=query,
                retrieved_contexts=retrieved_contexts,
                total_chunks_searched=total_chunks_searched,
                retrieval_time_ms=processing_time,
                retrieval_strategy=retrieval_type,
                confidence_score=confidence_score,
                metadata={
                    'document_types_searched': [dt.value for dt in document_types],
                    'score_threshold': score_threshold,
                    'max_contexts_requested': max_contexts
                }
            )
            
        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            return RAGResult(
                query=query,
                retrieved_contexts=[],
                total_chunks_searched=0,
                retrieval_time_ms=0,
                retrieval_strategy=retrieval_type,
                confidence_score=0.0,
                metadata={'error': str(e)}
            )
    
    async def _semantic_retrieval(
        self,
        query: str,
        document_types: List[DocumentType],
        max_contexts: int,
        score_threshold: float
    ) -> List[RetrievedContext]:
        """Perform semantic similarity search"""
        
        contexts = []
        
        for doc_type in document_types:
            index_name = f"{doc_type.value}_index"
            
            results = await self.vector_store.similarity_search(
                index_name, query, k=max_contexts, score_threshold=score_threshold
            )
            
            for doc, score in results:
                context = RetrievedContext(
                    content=doc.page_content,
                    source=doc.metadata.get('source', 'unknown'),
                    document_type=doc_type,
                    relevance_score=float(score),
                    chunk_index=doc.metadata.get('chunk_index', 0),
                    metadata=doc.metadata
                )
                contexts.append(context)
        
        # Sort by relevance score
        contexts.sort(key=lambda x: x.relevance_score, reverse=True)
        return contexts[:max_contexts]
    
    async def _keyword_retrieval(
        self,
        query: str,
        document_types: List[DocumentType],
        max_contexts: int,
        score_threshold: float
    ) -> List[RetrievedContext]:
        """Perform keyword-based search"""
        
        query_keywords = self.document_processor.extract_keywords(query)
        contexts = []
        
        for doc_type in document_types:
            documents = self.document_stores[doc_type]
            
            for doc in documents:
                doc_keywords = self.document_processor.extract_keywords(doc.page_content)
                
                # Calculate keyword overlap score
                overlap = len(set(query_keywords) & set(doc_keywords))
                score = overlap / max(len(query_keywords), 1)
                
                if score >= score_threshold:
                    context = RetrievedContext(
                        content=doc.page_content,
                        source=doc.metadata.get('source', 'unknown'),
                        document_type=doc_type,
                        relevance_score=score,
                        chunk_index=doc.metadata.get('chunk_index', 0),
                        metadata=doc.metadata
                    )
                    contexts.append(context)
        
        # Sort by relevance score
        contexts.sort(key=lambda x: x.relevance_score, reverse=True)
        return contexts[:max_contexts]
    
    async def _multi_query_retrieval(
        self,
        query: str,
        document_types: List[DocumentType],
        max_contexts: int,
        score_threshold: float
    ) -> List[RetrievedContext]:
        """Generate multiple query variations and retrieve contexts"""
        
        # Generate query variations using LLM
        variations = await self._generate_query_variations(query)
        
        all_contexts = []
        
        # Retrieve for each variation
        for variation in variations:
            contexts = await self._semantic_retrieval(
                variation, document_types, max_contexts // len(variations), score_threshold
            )
            all_contexts.extend(contexts)
        
        # Deduplicate and rank
        unique_contexts = self._deduplicate_contexts(all_contexts)
        return unique_contexts[:max_contexts]
    
    async def _contextual_retrieval(
        self,
        query: str,
        document_types: List[DocumentType],
        max_contexts: int,
        score_threshold: float
    ) -> List[RetrievedContext]:
        """Retrieve with contextual compression"""
        
        # First get more contexts than needed
        initial_contexts = await self._semantic_retrieval(
            query, document_types, max_contexts * 2, score_threshold * 0.5
        )
        
        # Use LLM to compress and rank contexts
        compressed_contexts = await self._compress_contexts(query, initial_contexts)
        
        return compressed_contexts[:max_contexts]
    
    async def _generate_query_variations(self, query: str) -> List[str]:
        """Generate query variations for multi-query retrieval"""
        
        prompt = f"""
        Generate 3 different variations of this query that capture the same intent:
        
        Original query: {query}
        
        Variations:
        1.
        2.
        3.
        """
        
        try:
            response = await self.llm_manager.generate_response(
                prompt, QueryType.GENERATION, system_message="Generate query variations only."
            )
            
            # Parse variations from response
            lines = response.content.strip().split('\n')
            variations = []
            
            for line in lines:
                if line.strip() and any(line.startswith(str(i)) for i in range(1, 4)):
                    variation = line.split('.', 1)[-1].strip()
                    if variation:
                        variations.append(variation)
            
            return variations if variations else [query]
            
        except Exception as e:
            logger.error(f"Query variation generation failed: {e}")
            return [query]
    
    async def _compress_contexts(
        self,
        query: str,
        contexts: List[RetrievedContext]
    ) -> List[RetrievedContext]:
        """Use LLM to compress and rank contexts"""
        
        if not contexts:
            return contexts
        
        # Prepare context summary for LLM
        context_summaries = []
        for i, ctx in enumerate(contexts):
            summary = f"{i+1}. Source: {ctx.source} | Score: {ctx.relevance_score:.2f}\n{ctx.content[:200]}..."
            context_summaries.append(summary)
        
        prompt = f"""
        Query: {query}
        
        Rank these contexts by relevance and compress them to the most important information:
        
        {chr(10).join(context_summaries)}
        
        Return the context numbers in order of relevance (most relevant first):
        """
        
        try:
            response = await self.llm_manager.generate_response(
                prompt, QueryType.ANALYSIS, system_message="Rank and analyze context relevance."
            )
            
            # Parse ranking from response
            ranking = self._parse_context_ranking(response.content, len(contexts))
            
            # Reorder contexts based on LLM ranking
            reordered_contexts = [contexts[i] for i in ranking if i < len(contexts)]
            
            return reordered_contexts
            
        except Exception as e:
            logger.error(f"Context compression failed: {e}")
            return contexts
    
    def _parse_context_ranking(self, response: str, num_contexts: int) -> List[int]:
        """Parse context ranking from LLM response"""
        ranking = []
        
        # Look for numbers in the response
        import re
        numbers = re.findall(r'\b\d+\b', response)
        
        for num_str in numbers:
            num = int(num_str)
            if 1 <= num <= num_contexts and (num - 1) not in ranking:
                ranking.append(num - 1)  # Convert to 0-based index
        
        # Add any missing indices
        for i in range(num_contexts):
            if i not in ranking:
                ranking.append(i)
        
        return ranking
    
    def _deduplicate_contexts(self, contexts: List[RetrievedContext]) -> List[RetrievedContext]:
        """Remove duplicate contexts based on content similarity"""
        
        if not contexts:
            return contexts
        
        unique_contexts = []
        seen_content = set()
        
        for context in contexts:
            # Create content fingerprint
            content_hash = hash(context.content[:100])  # Use first 100 chars
            
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_contexts.append(context)
        
        return unique_contexts
    
    def _calculate_retrieval_confidence(self, contexts: List[RetrievedContext]) -> float:
        """Calculate confidence score for retrieval results"""
        
        if not contexts:
            return 0.0
        
        # Base confidence on average relevance score and number of results
        avg_score = sum(ctx.relevance_score for ctx in contexts) / len(contexts)
        result_count_factor = min(len(contexts) / 5, 1.0)  # Optimal around 5 results
        
        confidence = (avg_score * 0.7) + (result_count_factor * 0.3)
        return min(confidence, 1.0)
    
    def _update_retrieval_stats(self, retrieval_type: RetrievalType, processing_time: int):
        """Update retrieval statistics"""
        self.retrieval_stats['total_queries'] += 1
        
        # Update average retrieval time
        total_queries = self.retrieval_stats['total_queries']
        current_avg = self.retrieval_stats['average_retrieval_time']
        new_avg = ((current_avg * (total_queries - 1)) + processing_time) / total_queries
        self.retrieval_stats['average_retrieval_time'] = new_avg
        
        # Update method-specific stats
        method = retrieval_type.value
        if method not in self.retrieval_stats['retrieval_methods']:
            self.retrieval_stats['retrieval_methods'][method] = {'count': 0, 'avg_time': 0.0}
        
        method_stats = self.retrieval_stats['retrieval_methods'][method]
        method_stats['count'] += 1
        method_avg = method_stats['avg_time']
        method_stats['avg_time'] = ((method_avg * (method_stats['count'] - 1)) + processing_time) / method_stats['count']
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAG pipeline statistics"""
        return {
            'retrieval_stats': dict(self.retrieval_stats),
            'document_counts': {dt.value: len(docs) for dt, docs in self.document_stores.items()},
            'vector_stores': list(self.vector_store.vector_stores.keys()),
            'total_indexed_chunks': sum(len(docs) for docs in self.document_stores.values())
        }