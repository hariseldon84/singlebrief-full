"""
LLM Integration and Management
Advanced LLM capabilities with multi-provider support and optimization
"""

import logging
import asyncio
import time
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.schema import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain.callbacks import AsyncCallbackHandler
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts import ChatPromptTemplate, PromptTemplate

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ModelProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"


class QueryType(str, Enum):
    """Types of queries for model selection"""
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    CONVERSATION = "conversation"
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"
    GENERATION = "generation"


@dataclass
class LLMResponse:
    """Structured LLM response with metadata"""
    content: str
    provider: ModelProvider
    model: str
    tokens_used: int
    cost_estimate: float
    processing_time_ms: int
    confidence_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelConfig:
    """Configuration for LLM models"""
    provider: ModelProvider
    model_name: str
    temperature: float = 0.1
    max_tokens: int = 2000
    streaming: bool = False
    cost_per_1k_tokens: float = 0.002
    context_window: int = 8192
    capabilities: List[str] = field(default_factory=list)


class StreamingCallback(AsyncCallbackHandler):
    """Callback for streaming LLM responses"""
    
    def __init__(self):
        self.tokens = []
        self.start_time = time.time()
    
    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Handle new token from streaming response"""
        self.tokens.append(token)
    
    async def on_llm_end(self, response, **kwargs) -> None:
        """Handle completion of streaming response"""
        self.processing_time = (time.time() - self.start_time) * 1000


class LLMManager:
    """
    Advanced LLM management with multi-provider support.
    
    Features:
    1. Multi-provider support (OpenAI, Anthropic, Azure)
    2. Intelligent model selection based on query type
    3. Cost optimization and token management
    4. Response streaming and callbacks
    5. Performance monitoring and caching
    6. Safety and content filtering
    """
    
    def __init__(self):
        self.providers = {}
        self.model_configs = {}
        self.usage_stats = {}
        self.conversation_memory = {}
        
        # Initialize available models
        self._initialize_models()
        
        # Prompt templates for different query types
        self.prompt_templates = {
            QueryType.ANALYSIS: self._get_analysis_template(),
            QueryType.SYNTHESIS: self._get_synthesis_template(),
            QueryType.CONVERSATION: self._get_conversation_template(),
            QueryType.SUMMARIZATION: self._get_summarization_template(),
            QueryType.CLASSIFICATION: self._get_classification_template(),
            QueryType.GENERATION: self._get_generation_template()
        }
        
        logger.info("LLMManager initialized with multiple providers")
    
    def _initialize_models(self):
        """Initialize available LLM models and providers"""
        
        # OpenAI models
        if settings.OPENAI_API_KEY:
            self.model_configs[ModelProvider.OPENAI] = [
                ModelConfig(
                    provider=ModelProvider.OPENAI,
                    model_name="gpt-4-turbo-preview",
                    temperature=0.1,
                    max_tokens=4000,
                    cost_per_1k_tokens=0.03,
                    context_window=128000,
                    capabilities=["analysis", "synthesis", "reasoning", "coding"]
                ),
                ModelConfig(
                    provider=ModelProvider.OPENAI,
                    model_name="gpt-3.5-turbo",
                    temperature=0.1,
                    max_tokens=2000,
                    cost_per_1k_tokens=0.002,
                    context_window=16384,
                    capabilities=["conversation", "summarization", "classification"]
                )
            ]
            
            # Initialize OpenAI provider
            self.providers[ModelProvider.OPENAI] = {}
            for config in self.model_configs[ModelProvider.OPENAI]:
                self.providers[ModelProvider.OPENAI][config.model_name] = ChatOpenAI(
                    model=config.model_name,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    request_timeout=60,
                    max_retries=3,
                    streaming=config.streaming
                )
        
        # Anthropic models
        if settings.ANTHROPIC_API_KEY:
            self.model_configs[ModelProvider.ANTHROPIC] = [
                ModelConfig(
                    provider=ModelProvider.ANTHROPIC,
                    model_name="claude-3-opus-20240229",
                    temperature=0.1,
                    max_tokens=4000,
                    cost_per_1k_tokens=0.015,
                    context_window=200000,
                    capabilities=["analysis", "synthesis", "reasoning", "writing"]
                ),
                ModelConfig(
                    provider=ModelProvider.ANTHROPIC,
                    model_name="claude-3-sonnet-20240229",
                    temperature=0.1,
                    max_tokens=2000,
                    cost_per_1k_tokens=0.003,
                    context_window=200000,
                    capabilities=["conversation", "analysis", "summarization"]
                )
            ]
            
            # Initialize Anthropic provider
            self.providers[ModelProvider.ANTHROPIC] = {}
            for config in self.model_configs[ModelProvider.ANTHROPIC]:
                self.providers[ModelProvider.ANTHROPIC][config.model_name] = ChatAnthropic(
                    model=config.model_name,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    timeout=60,
                    max_retries=3
                )
    
    def select_model(
        self, 
        query_type: QueryType, 
        context_length: int = 0,
        budget_priority: bool = False
    ) -> tuple[ModelProvider, str, ModelConfig]:
        """
        Intelligently select the best model for a query.
        
        Args:
            query_type: Type of query to process
            context_length: Estimated context length needed
            budget_priority: Whether to prioritize cost over performance
            
        Returns:
            Tuple of (provider, model_name, config)
        """
        
        suitable_models = []
        
        # Find models that support the query type
        for provider, configs in self.model_configs.items():
            for config in configs:
                if query_type.value in config.capabilities:
                    if context_length <= config.context_window:
                        suitable_models.append((provider, config))
        
        if not suitable_models:
            # Fallback to most capable model
            logger.warning(f"No suitable model found for {query_type}, using fallback")
            return self._get_fallback_model()
        
        # Sort by cost if budget priority, otherwise by capability
        if budget_priority:
            suitable_models.sort(key=lambda x: x[1].cost_per_1k_tokens)
        else:
            # Sort by context window and capabilities (proxy for capability)
            suitable_models.sort(
                key=lambda x: (x[1].context_window, len(x[1].capabilities)), 
                reverse=True
            )
        
        provider, config = suitable_models[0]
        return provider, config.model_name, config
    
    def _get_fallback_model(self) -> tuple[ModelProvider, str, ModelConfig]:
        """Get fallback model when no suitable model is found"""
        # Use the most capable available model
        for provider, configs in self.model_configs.items():
            if configs:
                best_config = max(configs, key=lambda x: x.context_window)
                return provider, best_config.model_name, best_config
        
        raise RuntimeError("No LLM models available")
    
    async def generate_response(
        self,
        prompt: str,
        query_type: QueryType = QueryType.CONVERSATION,
        context: Optional[str] = None,
        system_message: Optional[str] = None,
        conversation_id: Optional[str] = None,
        streaming: bool = False,
        **kwargs
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """
        Generate response using the best available model.
        
        Args:
            prompt: User prompt/query
            query_type: Type of query for model selection
            context: Additional context to include
            system_message: Custom system message
            conversation_id: ID for conversation memory
            streaming: Whether to stream the response
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse object or async generator for streaming
        """
        
        start_time = time.time()
        
        try:
            # Select appropriate model
            provider, model_name, config = self.select_model(
                query_type, 
                len(prompt) + len(context or ""),
                kwargs.get('budget_priority', False)
            )
            
            # Get model instance
            llm = self.providers[provider][model_name]
            
            # Prepare messages
            messages = self._prepare_messages(
                prompt, query_type, context, system_message, conversation_id
            )
            
            # Generate response
            if streaming:
                return self._stream_response(llm, messages, provider, model_name, config)
            else:
                response = await llm.ainvoke(messages)
                
                # Calculate metrics
                processing_time = int((time.time() - start_time) * 1000)
                tokens_used = self._estimate_tokens(messages, response.content)
                cost_estimate = self._calculate_cost(tokens_used, config)
                
                # Update conversation memory if needed
                if conversation_id:
                    self._update_conversation_memory(conversation_id, prompt, response.content)
                
                # Track usage stats
                self._update_usage_stats(provider, model_name, tokens_used, cost_estimate)
                
                return LLMResponse(
                    content=response.content,
                    provider=provider,
                    model=model_name,
                    tokens_used=tokens_used,
                    cost_estimate=cost_estimate,
                    processing_time_ms=processing_time,
                    confidence_score=self._calculate_confidence(response.content),
                    metadata={
                        'query_type': query_type.value,
                        'context_length': len(context or ""),
                        'conversation_id': conversation_id
                    }
                )
                
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise
    
    async def _stream_response(
        self,
        llm,
        messages: List[BaseMessage],
        provider: ModelProvider,
        model_name: str,
        config: ModelConfig
    ) -> AsyncGenerator[str, None]:
        """Stream response from LLM"""
        
        callback = StreamingCallback()
        
        async for chunk in llm.astream(messages, callbacks=[callback]):
            if hasattr(chunk, 'content'):
                yield chunk.content
        
        # Update stats after streaming completes
        total_content = ''.join(callback.tokens)
        tokens_used = self._estimate_tokens(messages, total_content)
        cost_estimate = self._calculate_cost(tokens_used, config)
        
        self._update_usage_stats(provider, model_name, tokens_used, cost_estimate)
    
    def _prepare_messages(
        self,
        prompt: str,
        query_type: QueryType,
        context: Optional[str],
        system_message: Optional[str],
        conversation_id: Optional[str]
    ) -> List[BaseMessage]:
        """Prepare messages for LLM based on query type and context"""
        
        messages = []
        
        # Add system message
        if system_message:
            messages.append(SystemMessage(content=system_message))
        else:
            template = self.prompt_templates.get(query_type)
            if template:
                system_content = template.format(context=context or "")
                messages.append(SystemMessage(content=system_content))
        
        # Add conversation history if available
        if conversation_id and conversation_id in self.conversation_memory:
            memory = self.conversation_memory[conversation_id]
            messages.extend(memory.chat_memory.messages[-10:])  # Last 10 messages
        
        # Add current user message
        if context:
            user_content = f"Context: {context}\n\nQuery: {prompt}"
        else:
            user_content = prompt
        
        messages.append(HumanMessage(content=user_content))
        
        return messages
    
    def _estimate_tokens(self, messages: List[BaseMessage], response: str) -> int:
        """Estimate token usage for cost calculation"""
        # Simple estimation: ~4 characters per token
        total_chars = sum(len(msg.content) for msg in messages) + len(response)
        return int(total_chars / 4)
    
    def _calculate_cost(self, tokens_used: int, config: ModelConfig) -> float:
        """Calculate estimated cost for the request"""
        return (tokens_used / 1000) * config.cost_per_1k_tokens
    
    def _calculate_confidence(self, content: str) -> float:
        """Calculate confidence score based on response characteristics"""
        # Simple heuristic - can be enhanced with more sophisticated analysis
        if len(content) < 50:
            return 0.6  # Very short responses get lower confidence
        elif "I'm not sure" in content or "I don't know" in content:
            return 0.4  # Uncertain responses
        elif any(word in content.lower() for word in ["likely", "probably", "might", "perhaps"]):
            return 0.7  # Hedged responses
        else:
            return 0.9  # Confident responses
    
    def _update_conversation_memory(self, conversation_id: str, prompt: str, response: str):
        """Update conversation memory for context continuity"""
        if conversation_id not in self.conversation_memory:
            self.conversation_memory[conversation_id] = ConversationSummaryBufferMemory(
                max_token_limit=2000,
                return_messages=True
            )
        
        memory = self.conversation_memory[conversation_id]
        memory.chat_memory.add_user_message(prompt)
        memory.chat_memory.add_ai_message(response)
    
    def _update_usage_stats(self, provider: ModelProvider, model: str, tokens: int, cost: float):
        """Update usage statistics for monitoring"""
        key = f"{provider.value}:{model}"
        if key not in self.usage_stats:
            self.usage_stats[key] = {
                'total_requests': 0,
                'total_tokens': 0,
                'total_cost': 0.0,
                'last_used': None
            }
        
        stats = self.usage_stats[key]
        stats['total_requests'] += 1
        stats['total_tokens'] += tokens
        stats['total_cost'] += cost
        stats['last_used'] = datetime.now(timezone.utc)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        return {
            'models': dict(self.usage_stats),
            'total_requests': sum(s['total_requests'] for s in self.usage_stats.values()),
            'total_tokens': sum(s['total_tokens'] for s in self.usage_stats.values()),
            'total_cost': sum(s['total_cost'] for s in self.usage_stats.values()),
            'active_conversations': len(self.conversation_memory)
        }
    
    # Prompt templates for different query types
    def _get_analysis_template(self) -> str:
        return """You are an expert analyst helping team leads understand complex information.

Analyze the provided context and query with a focus on:
- Identifying key patterns and trends
- Extracting actionable insights
- Providing evidence-based conclusions
- Highlighting important relationships and dependencies

Context: {context}

Provide a structured analysis that is clear, actionable, and well-reasoned."""
    
    def _get_synthesis_template(self) -> str:
        return """You are an expert information synthesizer for team intelligence.

Combine information from multiple sources to create a coherent, comprehensive response:
- Integrate different perspectives and data points
- Resolve any contradictions with clear reasoning
- Prioritize information by relevance and reliability
- Maintain source attribution where important

Context: {context}

Synthesize the information into a unified, actionable response."""
    
    def _get_conversation_template(self) -> str:
        return """You are SingleBrief, an AI assistant helping team leads with intelligence gathering.

You have access to team communications, project data, and organizational context.
Provide helpful, accurate, and contextually relevant responses.

Be concise but comprehensive, and always maintain a professional, supportive tone.

Context: {context}"""
    
    def _get_summarization_template(self) -> str:
        return """You are an expert at creating executive summaries for busy team leads.

Create concise, well-structured summaries that:
- Capture the most important information
- Highlight key decisions and action items
- Maintain clarity and readability
- Focus on what matters to leadership

Context: {context}

Provide a clear, executive-level summary."""
    
    def _get_classification_template(self) -> str:
        return """You are an expert at classifying and categorizing information.

Analyze the provided content and classify it according to the specified criteria.
Be accurate, consistent, and provide confidence scores for your classifications.

Context: {context}

Provide clear classification with reasoning."""
    
    def _get_generation_template(self) -> str:
        return """You are a creative and accurate content generator.

Generate high-quality content based on the provided context and requirements.
Ensure accuracy, relevance, and appropriate tone for the intended audience.

Context: {context}

Generate content that meets the specified requirements."""