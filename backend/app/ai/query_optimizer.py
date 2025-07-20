"""
Query Processing Optimization System
Advanced query analysis, caching, and performance optimization
"""

import logging
import asyncio
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
import json

from app.ai.llm_integration import LLMManager, QueryType
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class QueryComplexity(str, Enum):
    """Query complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class OptimizationStrategy(str, Enum):
    """Optimization strategies for queries"""
    CACHE_FIRST = "cache_first"
    PARALLEL_PROCESSING = "parallel_processing"
    INCREMENTAL_LOADING = "incremental_loading"
    QUERY_DECOMPOSITION = "query_decomposition"
    SMART_ROUTING = "smart_routing"


class CacheStrategy(str, Enum):
    """Caching strategies"""
    NO_CACHE = "no_cache"
    SHORT_TERM = "short_term"
    MEDIUM_TERM = "medium_term"
    LONG_TERM = "long_term"
    SMART_CACHE = "smart_cache"


@dataclass
class QueryAnalysis:
    """Analysis results for a query"""
    query: str
    query_hash: str
    complexity: QueryComplexity
    estimated_processing_time: float
    required_modules: List[str]
    optimization_strategies: List[OptimizationStrategy]
    cache_strategy: CacheStrategy
    priority_score: float
    decomposed_subqueries: List[str]
    analysis_metadata: Dict[str, Any]


@dataclass
class CacheEntry:
    """Cache entry for query results"""
    query_hash: str
    original_query: str
    result: Dict[str, Any]
    cached_at: datetime
    access_count: int
    last_accessed: datetime
    ttl_seconds: int
    cache_strategy: CacheStrategy
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return datetime.now(timezone.utc) > self.cached_at + timedelta(seconds=self.ttl_seconds)
    
    @property
    def freshness_score(self) -> float:
        """Calculate freshness score (0.0 to 1.0)"""
        age_seconds = (datetime.now(timezone.utc) - self.cached_at).total_seconds()
        return max(0.0, 1.0 - (age_seconds / self.ttl_seconds))


@dataclass
class PerformanceMetrics:
    """Performance metrics for query processing"""
    query_hash: str
    processing_time_ms: int
    cache_hit: bool
    modules_used: List[str]
    optimization_strategies_applied: List[OptimizationStrategy]
    token_usage: int
    cost_estimate: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class QueryCache:
    """Advanced caching system for query results"""
    
    def __init__(self, max_size: int = 10000):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        
        # TTL configurations by strategy
        self.ttl_configs = {
            CacheStrategy.SHORT_TERM: 300,      # 5 minutes
            CacheStrategy.MEDIUM_TERM: 3600,    # 1 hour
            CacheStrategy.LONG_TERM: 86400,     # 24 hours
            CacheStrategy.SMART_CACHE: 7200     # 2 hours default for smart
        }
        
        # Cache statistics
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'evictions': 0,
            'total_size': 0
        }
        
        logger.info(f"Query cache initialized with max size: {max_size}")
    
    def get(self, query_hash: str) -> Optional[CacheEntry]:
        """Get entry from cache"""
        self.stats['total_requests'] += 1
        
        if query_hash in self.cache:
            entry = self.cache[query_hash]
            
            if entry.is_expired:
                del self.cache[query_hash]
                self.stats['cache_misses'] += 1
                return None
            
            # Update access metrics
            entry.access_count += 1
            entry.last_accessed = datetime.now(timezone.utc)
            self.stats['cache_hits'] += 1
            
            return entry
        
        self.stats['cache_misses'] += 1
        return None
    
    def put(
        self, 
        query_hash: str, 
        query: str, 
        result: Dict[str, Any], 
        cache_strategy: CacheStrategy,
        custom_ttl: Optional[int] = None
    ):
        """Put entry in cache"""
        
        # Determine TTL
        ttl_seconds = custom_ttl or self.ttl_configs.get(cache_strategy, 3600)
        
        # Create cache entry
        entry = CacheEntry(
            query_hash=query_hash,
            original_query=query,
            result=result,
            cached_at=datetime.now(timezone.utc),
            access_count=0,
            last_accessed=datetime.now(timezone.utc),
            ttl_seconds=ttl_seconds,
            cache_strategy=cache_strategy
        )
        
        # Check if we need to evict entries
        if len(self.cache) >= self.max_size:
            self._evict_entries()
        
        self.cache[query_hash] = entry
        self.stats['total_size'] = len(self.cache)
    
    def _evict_entries(self):
        """Evict least recently used entries"""
        
        # Sort by last accessed time and access count
        entries_by_lru = sorted(
            self.cache.items(),
            key=lambda x: (x[1].last_accessed, x[1].access_count)
        )
        
        # Remove oldest 20% of entries
        evict_count = max(1, len(entries_by_lru) // 5)
        
        for i in range(evict_count):
            query_hash, _ = entries_by_lru[i]
            del self.cache[query_hash]
            self.stats['evictions'] += 1
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching a pattern"""
        
        to_remove = []
        for query_hash, entry in self.cache.items():
            if pattern.lower() in entry.original_query.lower():
                to_remove.append(query_hash)
        
        for query_hash in to_remove:
            del self.cache[query_hash]
        
        logger.info(f"Invalidated {len(to_remove)} cache entries matching pattern: {pattern}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        
        hit_rate = self.stats['cache_hits'] / max(self.stats['total_requests'], 1)
        
        return {
            **self.stats,
            'hit_rate': hit_rate,
            'current_size': len(self.cache),
            'strategy_distribution': self._get_strategy_distribution()
        }
    
    def _get_strategy_distribution(self) -> Dict[str, int]:
        """Get distribution of cache strategies"""
        
        distribution = {}
        for entry in self.cache.values():
            strategy = entry.cache_strategy.value
            distribution[strategy] = distribution.get(strategy, 0) + 1
        
        return distribution


class QueryAnalyzer:
    """Advanced query analysis for optimization"""
    
    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager
        
        # Complexity indicators
        self.complexity_indicators = {
            'keywords': {
                'simple': ['status', 'what', 'who', 'when', 'where'],
                'moderate': ['analyze', 'compare', 'explain', 'summarize'],
                'complex': ['comprehensive', 'detailed', 'thorough', 'deep'],
                'very_complex': ['synthesis', 'correlation', 'prediction', 'optimization']
            },
            'length_thresholds': {
                'simple': 50,
                'moderate': 150,
                'complex': 300,
                'very_complex': 500
            }
        }
        
        # Module mapping for different query types
        self.module_mapping = {
            'team': ['team_comms_crawler', 'memory_engine'],
            'project': ['integration_hub', 'team_comms_crawler'],
            'status': ['team_comms_crawler', 'integration_hub'],
            'analysis': ['memory_engine', 'integration_hub', 'trust_layer'],
            'synthesis': ['team_comms_crawler', 'memory_engine', 'integration_hub', 'trust_layer']
        }
    
    async def analyze_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> QueryAnalysis:
        """Comprehensive query analysis for optimization"""
        
        try:
            # Generate query hash
            query_hash = hashlib.md5(query.encode()).hexdigest()
            
            # Analyze complexity
            complexity = self._analyze_complexity(query)
            
            # Estimate processing time
            estimated_time = self._estimate_processing_time(query, complexity, context)
            
            # Determine required modules
            required_modules = self._determine_required_modules(query)
            
            # Select optimization strategies
            optimization_strategies = self._select_optimization_strategies(query, complexity, estimated_time)
            
            # Determine cache strategy
            cache_strategy = self._determine_cache_strategy(query, complexity, context)
            
            # Calculate priority score
            priority_score = self._calculate_priority_score(query, complexity, context)
            
            # Decompose complex queries
            decomposed_subqueries = await self._decompose_query(query, complexity)
            
            return QueryAnalysis(
                query=query,
                query_hash=query_hash,
                complexity=complexity,
                estimated_processing_time=estimated_time,
                required_modules=required_modules,
                optimization_strategies=optimization_strategies,
                cache_strategy=cache_strategy,
                priority_score=priority_score,
                decomposed_subqueries=decomposed_subqueries,
                analysis_metadata={
                    'analyzed_at': datetime.now(timezone.utc).isoformat(),
                    'context_provided': context is not None,
                    'query_length': len(query),
                    'word_count': len(query.split())
                }
            )
            
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            raise
    
    def _analyze_complexity(self, query: str) -> QueryComplexity:
        """Analyze query complexity"""
        
        query_lower = query.lower()
        query_length = len(query)
        word_count = len(query.split())
        
        # Check for complexity keywords
        complexity_score = 0
        
        for complexity_level, keywords in self.complexity_indicators['keywords'].items():
            for keyword in keywords:
                if keyword in query_lower:
                    if complexity_level == 'simple':
                        complexity_score += 1
                    elif complexity_level == 'moderate':
                        complexity_score += 2
                    elif complexity_level == 'complex':
                        complexity_score += 3
                    elif complexity_level == 'very_complex':
                        complexity_score += 4
        
        # Factor in length
        length_score = 0
        if query_length > self.complexity_indicators['length_thresholds']['very_complex']:
            length_score = 4
        elif query_length > self.complexity_indicators['length_thresholds']['complex']:
            length_score = 3
        elif query_length > self.complexity_indicators['length_thresholds']['moderate']:
            length_score = 2
        else:
            length_score = 1
        
        # Combine scores
        total_score = (complexity_score + length_score + word_count // 10) / 3
        
        if total_score >= 4:
            return QueryComplexity.VERY_COMPLEX
        elif total_score >= 3:
            return QueryComplexity.COMPLEX
        elif total_score >= 2:
            return QueryComplexity.MODERATE
        else:
            return QueryComplexity.SIMPLE
    
    def _estimate_processing_time(
        self, 
        query: str, 
        complexity: QueryComplexity, 
        context: Optional[Dict[str, Any]]
    ) -> float:
        """Estimate query processing time in seconds"""
        
        base_times = {
            QueryComplexity.SIMPLE: 2.0,
            QueryComplexity.MODERATE: 5.0,
            QueryComplexity.COMPLEX: 10.0,
            QueryComplexity.VERY_COMPLEX: 20.0
        }
        
        base_time = base_times[complexity]
        
        # Adjust for context factors
        if context:
            # More context means potentially faster processing due to specificity
            context_factor = max(0.7, 1.0 - len(context) * 0.1)
            base_time *= context_factor
        
        # Adjust for query characteristics
        if 'urgent' in query.lower() or 'asap' in query.lower():
            base_time *= 0.8  # Prioritize urgent queries
        
        if any(word in query.lower() for word in ['comprehensive', 'detailed', 'thorough']):
            base_time *= 1.5  # More thorough analysis takes longer
        
        return base_time
    
    def _determine_required_modules(self, query: str) -> List[str]:
        """Determine which modules are required for the query"""
        
        query_lower = query.lower()
        required_modules = set()
        
        # Map query keywords to modules
        for domain, modules in self.module_mapping.items():
            if domain in query_lower:
                required_modules.update(modules)
        
        # Default modules if none matched
        if not required_modules:
            required_modules = {'team_comms_crawler', 'memory_engine'}
        
        # Always include trust layer for confidence scoring
        required_modules.add('trust_layer')
        
        return list(required_modules)
    
    def _select_optimization_strategies(
        self, 
        query: str, 
        complexity: QueryComplexity, 
        estimated_time: float
    ) -> List[OptimizationStrategy]:
        """Select appropriate optimization strategies"""
        
        strategies = []
        
        # Cache strategy for repeated queries
        strategies.append(OptimizationStrategy.CACHE_FIRST)
        
        # Parallel processing for complex queries
        if complexity in [QueryComplexity.COMPLEX, QueryComplexity.VERY_COMPLEX]:
            strategies.append(OptimizationStrategy.PARALLEL_PROCESSING)
        
        # Query decomposition for very complex queries
        if complexity == QueryComplexity.VERY_COMPLEX:
            strategies.append(OptimizationStrategy.QUERY_DECOMPOSITION)
        
        # Incremental loading for long processing times
        if estimated_time > 10.0:
            strategies.append(OptimizationStrategy.INCREMENTAL_LOADING)
        
        # Smart routing for all queries
        strategies.append(OptimizationStrategy.SMART_ROUTING)
        
        return strategies
    
    def _determine_cache_strategy(
        self, 
        query: str, 
        complexity: QueryComplexity, 
        context: Optional[Dict[str, Any]]
    ) -> CacheStrategy:
        """Determine appropriate cache strategy"""
        
        query_lower = query.lower()
        
        # No cache for time-sensitive queries
        if any(word in query_lower for word in ['now', 'current', 'latest', 'urgent']):
            return CacheStrategy.NO_CACHE
        
        # Long-term cache for stable information
        if any(word in query_lower for word in ['policy', 'documentation', 'procedure']):
            return CacheStrategy.LONG_TERM
        
        # Medium-term cache for project information
        if any(word in query_lower for word in ['project', 'milestone', 'roadmap']):
            return CacheStrategy.MEDIUM_TERM
        
        # Short-term cache for team status
        if any(word in query_lower for word in ['team', 'status', 'progress']):
            return CacheStrategy.SHORT_TERM
        
        # Smart cache for complex queries
        if complexity in [QueryComplexity.COMPLEX, QueryComplexity.VERY_COMPLEX]:
            return CacheStrategy.SMART_CACHE
        
        return CacheStrategy.MEDIUM_TERM
    
    def _calculate_priority_score(
        self, 
        query: str, 
        complexity: QueryComplexity, 
        context: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate priority score for query processing"""
        
        base_score = 0.5
        query_lower = query.lower()
        
        # Urgency indicators
        if any(word in query_lower for word in ['urgent', 'asap', 'critical', 'emergency']):
            base_score += 0.4
        elif any(word in query_lower for word in ['important', 'priority', 'needed']):
            base_score += 0.2
        
        # Complexity adjustment
        complexity_adjustments = {
            QueryComplexity.SIMPLE: 0.1,
            QueryComplexity.MODERATE: 0.0,
            QueryComplexity.COMPLEX: -0.1,
            QueryComplexity.VERY_COMPLEX: -0.2
        }
        base_score += complexity_adjustments[complexity]
        
        # Context availability
        if context:
            base_score += 0.1
        
        return max(0.0, min(1.0, base_score))
    
    async def _decompose_query(self, query: str, complexity: QueryComplexity) -> List[str]:
        """Decompose complex queries into simpler subqueries"""
        
        if complexity not in [QueryComplexity.COMPLEX, QueryComplexity.VERY_COMPLEX]:
            return []
        
        prompt = f"""
        Break down this complex query into 2-4 simpler, more focused subqueries that can be processed independently:
        
        Original query: {query}
        
        Create subqueries that:
        1. Are specific and focused
        2. Can be answered independently
        3. Together provide information to answer the original query
        
        Format as a numbered list.
        """
        
        try:
            response = await self.llm_manager.generate_response(
                prompt, QueryType.ANALYSIS,
                system_message="Decompose queries into focused, answerable parts."
            )
            
            # Parse subqueries from response
            subqueries = []
            lines = response.content.split('\n')
            
            for line in lines:
                line = line.strip()
                if line and any(line.startswith(str(i)) for i in range(1, 10)):
                    subquery = line.split('.', 1)[-1].strip()
                    if subquery:
                        subqueries.append(subquery)
            
            return subqueries
            
        except Exception as e:
            logger.error(f"Query decomposition failed: {e}")
            return []


class QueryOptimizer:
    """
    Advanced query processing optimization system.
    
    Features:
    1. Intelligent query analysis and complexity assessment
    2. Multi-level caching with smart invalidation
    3. Query decomposition for complex requests
    4. Performance monitoring and optimization
    5. Adaptive processing strategies
    6. Cost optimization and resource management
    """
    
    def __init__(self):
        self.cache = QueryCache()
        self.llm_manager = LLMManager()
        self.query_analyzer = QueryAnalyzer(self.llm_manager)
        
        # Performance tracking
        self.performance_history: List[PerformanceMetrics] = []
        
        # Optimization settings
        self.settings = {
            'enable_caching': True,
            'enable_query_decomposition': True,
            'enable_parallel_processing': True,
            'max_cache_size': 10000,
            'performance_threshold_ms': 5000
        }
        
        logger.info("Query Optimizer initialized")
    
    async def optimize_query_processing(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        force_refresh: bool = False
    ) -> Tuple[QueryAnalysis, Optional[Dict[str, Any]]]:
        """
        Optimize query processing with caching and analysis.
        
        Args:
            query: Query to process
            context: Additional context
            force_refresh: Skip cache and force fresh processing
            
        Returns:
            Tuple of (QueryAnalysis, cached_result_if_available)
        """
        
        start_time = time.time()
        
        try:
            # Analyze query
            analysis = await self.query_analyzer.analyze_query(query, context)
            
            # Check cache if caching is enabled and not forcing refresh
            cached_result = None
            cache_hit = False
            
            if (self.settings['enable_caching'] and 
                not force_refresh and 
                analysis.cache_strategy != CacheStrategy.NO_CACHE):
                
                cached_entry = self.cache.get(analysis.query_hash)
                if cached_entry:
                    cached_result = cached_entry.result
                    cache_hit = True
                    logger.info(f"Cache hit for query: {query[:50]}...")
            
            # Record performance metrics
            processing_time = int((time.time() - start_time) * 1000)
            
            metrics = PerformanceMetrics(
                query_hash=analysis.query_hash,
                processing_time_ms=processing_time,
                cache_hit=cache_hit,
                modules_used=analysis.required_modules,
                optimization_strategies_applied=analysis.optimization_strategies,
                token_usage=0,  # Will be updated by actual processing
                cost_estimate=0.0  # Will be updated by actual processing
            )
            
            self.performance_history.append(metrics)
            
            return analysis, cached_result
            
        except Exception as e:
            logger.error(f"Query optimization failed: {e}")
            raise
    
    def cache_result(
        self,
        analysis: QueryAnalysis,
        result: Dict[str, Any],
        processing_metrics: Optional[Dict[str, Any]] = None
    ):
        """Cache query result with appropriate strategy"""
        
        if not self.settings['enable_caching'] or analysis.cache_strategy == CacheStrategy.NO_CACHE:
            return
        
        try:
            # Determine custom TTL based on result characteristics
            custom_ttl = None
            
            if analysis.cache_strategy == CacheStrategy.SMART_CACHE:
                # Smart TTL based on content freshness and update frequency
                if processing_metrics:
                    data_freshness = processing_metrics.get('data_freshness', 0.5)
                    # Fresher data gets longer cache time
                    custom_ttl = int(3600 * (1 + data_freshness))
            
            self.cache.put(
                analysis.query_hash,
                analysis.query,
                result,
                analysis.cache_strategy,
                custom_ttl
            )
            
            logger.info(f"Cached result for query: {analysis.query[:50]}...")
            
        except Exception as e:
            logger.error(f"Result caching failed: {e}")
    
    def invalidate_cache_for_updates(self, update_context: Dict[str, Any]):
        """Intelligently invalidate cache based on data updates"""
        
        try:
            # Invalidate based on update context
            if 'team_update' in update_context:
                self.cache.invalidate_pattern('team')
                self.cache.invalidate_pattern('status')
            
            if 'project_update' in update_context:
                self.cache.invalidate_pattern('project')
                self.cache.invalidate_pattern('milestone')
            
            if 'integration_update' in update_context:
                self.cache.invalidate_pattern('integration')
                self.cache.invalidate_pattern('data')
            
            logger.info(f"Cache invalidated for update context: {update_context}")
            
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
    
    async def optimize_subquery_processing(
        self,
        subqueries: List[str],
        original_context: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, QueryAnalysis]]:
        """Optimize processing of decomposed subqueries"""
        
        if not subqueries:
            return []
        
        try:
            subquery_analyses = []
            
            # Analyze all subqueries
            for subquery in subqueries:
                analysis = await self.query_analyzer.analyze_query(subquery, original_context)
                subquery_analyses.append((subquery, analysis))
            
            # Sort by priority and complexity for optimal processing order
            subquery_analyses.sort(
                key=lambda x: (x[1].priority_score, x[1].complexity.value),
                reverse=True
            )
            
            return subquery_analyses
            
        except Exception as e:
            logger.error(f"Subquery optimization failed: {e}")
            return [(sq, None) for sq in subqueries]
    
    def update_performance_metrics(
        self,
        query_hash: str,
        token_usage: int,
        cost_estimate: float,
        actual_processing_time: int
    ):
        """Update performance metrics after processing"""
        
        # Find the corresponding metrics entry
        for metrics in reversed(self.performance_history):
            if metrics.query_hash == query_hash:
                metrics.token_usage = token_usage
                metrics.cost_estimate = cost_estimate
                # Update processing time if actual time is different
                if actual_processing_time > metrics.processing_time_ms:
                    metrics.processing_time_ms = actual_processing_time
                break
    
    def get_optimization_statistics(self) -> Dict[str, Any]:
        """Get comprehensive optimization statistics"""
        
        if not self.performance_history:
            return {'message': 'No performance data available'}
        
        recent_metrics = self.performance_history[-100:]  # Last 100 queries
        
        # Calculate statistics
        processing_times = [m.processing_time_ms for m in recent_metrics]
        cache_hits = len([m for m in recent_metrics if m.cache_hit])
        total_queries = len(recent_metrics)
        
        avg_processing_time = sum(processing_times) / len(processing_times)
        cache_hit_rate = cache_hits / total_queries if total_queries > 0 else 0
        
        # Cost statistics
        total_cost = sum(m.cost_estimate for m in recent_metrics)
        total_tokens = sum(m.token_usage for m in recent_metrics)
        
        # Performance trends
        performance_trend = processing_times[-10:] if len(processing_times) >= 10 else processing_times
        
        return {
            'performance_metrics': {
                'total_queries_processed': len(self.performance_history),
                'recent_queries': total_queries,
                'average_processing_time_ms': avg_processing_time,
                'cache_hit_rate': cache_hit_rate,
                'performance_trend': performance_trend
            },
            'cost_metrics': {
                'total_cost_recent': total_cost,
                'total_tokens_recent': total_tokens,
                'average_cost_per_query': total_cost / total_queries if total_queries > 0 else 0
            },
            'cache_statistics': self.cache.get_cache_stats(),
            'optimization_settings': self.settings
        }
    
    def adjust_optimization_settings(self, new_settings: Dict[str, Any]):
        """Adjust optimization settings dynamically"""
        
        for key, value in new_settings.items():
            if key in self.settings:
                self.settings[key] = value
                logger.info(f"Updated optimization setting {key} to {value}")
        
        # Apply cache size changes
        if 'max_cache_size' in new_settings:
            self.cache.max_size = new_settings['max_cache_size']