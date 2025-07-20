"""
Query Parser for Orchestrator
Natural language query parsing and intent recognition
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class QueryIntent(BaseModel):
    """Structured query intent"""
    primary_intent: str = Field(description="Primary intent of the query")
    secondary_intents: List[str] = Field(default=[], description="Secondary intents")
    entities: List[Dict[str, str]] = Field(default=[], description="Named entities found")
    time_context: Optional[str] = Field(default=None, description="Time context if any")
    urgency: str = Field(default="normal", description="Urgency level: low, normal, high, urgent")
    scope: str = Field(default="team", description="Scope: personal, team, organization, project")
    query_type: str = Field(description="Type of query: status, update, question, command")


@dataclass
class ParsedQuery:
    """Complete parsed query with all analysis"""
    original_query: str
    intent: QueryIntent
    complexity_score: float
    confidence: float
    modules_needed: List[str]
    processing_hints: Dict[str, Any]
    metadata: Dict[str, Any]


class QueryParser:
    """
    Advanced query parser using LLM for intent recognition.
    
    Analyzes user queries to:
    1. Extract intent and entities
    2. Determine query complexity
    3. Identify required modules
    4. Provide processing hints
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.1,
            max_tokens=1000
        )
        
        self.output_parser = PydanticOutputParser(pydantic_object=QueryIntent)
        
        # Intent patterns for quick classification
        self.intent_patterns = {
            'team_status': [
                r'\b(how is|what\'s|status of|update on).*(team|everyone|people)',
                r'\b(team|everyone).*(doing|working|progress)',
                r'\bteam\s+(status|update|progress)',
            ],
            'project_status': [
                r'\b(project|sprint|release).*(status|progress|update)',
                r'\bhow.*(project|sprint|development)',
                r'\bwhat\'s.*(happening|going on).*(project|development)',
            ],
            'daily_brief': [
                r'\b(daily|today|this\s+morning).*(brief|update|summary)',
                r'\bwhat.*happened.*(today|yesterday)',
                r'\b(brief|summary|digest).*today',
            ],
            'meeting_info': [
                r'\b(meeting|call|standup).*(today|tomorrow|this\s+week)',
                r'\bwhat.*meetings',
                r'\bwhen.*(next|upcoming).*meeting',
            ],
            'individual_status': [
                r'\bhow.*(is|doing).*(john|sarah|mike|team\s+member)',
                r'\bwhat.*(working\s+on|doing).*(person|individual)',
                r'\b(where|status).*(specific\s+person)',
            ],
            'blockers': [
                r'\b(blocker|blocked|issue|problem|stuck)',
                r'\bwhat.*blocking',
                r'\bany.*(issue|problem|concern)',
            ],
            'decisions': [
                r'\b(decision|decided|choose|choice)',
                r'\bwhat.*decided',
                r'\b(recent|latest).*(decision|choice)',
            ]
        }
        
        # Module mapping based on intent
        self.intent_to_modules = {
            'team_status': ['team_comms_crawler', 'memory_engine'],
            'project_status': ['integration_hub', 'team_comms_crawler'],
            'daily_brief': ['team_comms_crawler', 'memory_engine', 'integration_hub'],
            'meeting_info': ['team_comms_crawler', 'integration_hub'],
            'individual_status': ['team_comms_crawler', 'memory_engine'],
            'blockers': ['team_comms_crawler', 'integration_hub'],
            'decisions': ['memory_engine', 'team_comms_crawler'],
            'memory_query': ['memory_engine'],
            'integration_status': ['integration_hub']
        }
        
        logger.info("QueryParser initialized")
    
    async def parse(self, query: str, context: Any) -> Dict[str, Any]:
        """
        Parse a natural language query into structured format.
        
        Args:
            query: Natural language query
            context: Query context
            
        Returns:
            Dictionary with parsed query information
        """
        try:
            # Quick pattern-based intent detection
            quick_intent = self._detect_intent_patterns(query)
            
            # LLM-based detailed analysis
            llm_intent = await self._analyze_with_llm(query)
            
            # Combine and validate results
            final_intent = self._merge_intent_analysis(quick_intent, llm_intent)
            
            # Calculate complexity
            complexity = self._calculate_complexity(query, final_intent)
            
            # Determine required modules
            modules_needed = self._determine_modules(final_intent)
            
            # Generate processing hints
            processing_hints = self._generate_processing_hints(query, final_intent)
            
            parsed_query = {
                'original_query': query,
                'intent': final_intent,
                'complexity_score': complexity,
                'confidence': llm_intent.get('confidence', 0.8),
                'modules_needed': modules_needed,
                'processing_hints': processing_hints,
                'metadata': {
                    'query_length': len(query),
                    'word_count': len(query.split()),
                    'has_time_context': bool(final_intent.get('time_context')),
                    'parsed_at': datetime.now(timezone.utc).isoformat()
                }
            }
            
            logger.info(f"Parsed query with intent: {final_intent.get('primary_intent')}")
            return parsed_query
            
        except Exception as e:
            logger.error(f"Query parsing failed: {e}")
            # Return fallback parsing
            return self._create_fallback_parse(query)
    
    def _detect_intent_patterns(self, query: str) -> Dict[str, Any]:
        """Quick pattern-based intent detection"""
        query_lower = query.lower()
        detected_intents = []
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    detected_intents.append(intent)
                    break
        
        # Extract time context
        time_context = self._extract_time_context(query_lower)
        
        # Determine urgency
        urgency = self._detect_urgency(query_lower)
        
        return {
            'primary_intent': detected_intents[0] if detected_intents else 'general_query',
            'secondary_intents': detected_intents[1:] if len(detected_intents) > 1 else [],
            'time_context': time_context,
            'urgency': urgency,
            'scope': self._detect_scope(query_lower)
        }
    
    async def _analyze_with_llm(self, query: str) -> Dict[str, Any]:
        """Use LLM for detailed query analysis"""
        system_prompt = """
You are an expert at analyzing queries for a team intelligence system. 
Analyze the given query and extract:

1. Primary intent (what the user mainly wants)
2. Secondary intents (additional things they might want)
3. Named entities (people, projects, dates, etc.)
4. Time context (when, if specified)
5. Urgency level (low, normal, high, urgent)
6. Scope (personal, team, organization, project)
7. Query type (status, update, question, command)

Focus on understanding what a team lead or manager would want to know.

{format_instructions}
"""
        
        try:
            messages = [
                SystemMessage(content=system_prompt.format(
                    format_instructions=self.output_parser.get_format_instructions()
                )),
                HumanMessage(content=f"Query: {query}")
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Parse the response
            parsed_intent = self.output_parser.parse(response.content)
            
            return {
                'primary_intent': parsed_intent.primary_intent,
                'secondary_intents': parsed_intent.secondary_intents,
                'entities': parsed_intent.entities,
                'time_context': parsed_intent.time_context,
                'urgency': parsed_intent.urgency,
                'scope': parsed_intent.scope,
                'query_type': parsed_intent.query_type,
                'confidence': 0.9  # High confidence for LLM analysis
            }
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {'confidence': 0.3}  # Low confidence fallback
    
    def _merge_intent_analysis(
        self, 
        pattern_result: Dict[str, Any], 
        llm_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge pattern-based and LLM-based analysis"""
        
        # Start with LLM result as base (higher accuracy)
        merged = llm_result.copy() if llm_result.get('confidence', 0) > 0.5 else pattern_result.copy()
        
        # Use pattern result as fallback/validation
        if not merged.get('primary_intent'):
            merged['primary_intent'] = pattern_result.get('primary_intent', 'general_query')
        
        if not merged.get('time_context') and pattern_result.get('time_context'):
            merged['time_context'] = pattern_result['time_context']
        
        if not merged.get('urgency'):
            merged['urgency'] = pattern_result.get('urgency', 'normal')
        
        return merged
    
    def _extract_time_context(self, query: str) -> Optional[str]:
        """Extract time context from query"""
        time_patterns = {
            'today': r'\b(today|this\s+morning|this\s+afternoon|right\s+now)',
            'yesterday': r'\b(yesterday|last\s+night)',
            'this_week': r'\b(this\s+week|past\s+week)',
            'last_week': r'\b(last\s+week|previous\s+week)',
            'recent': r'\b(recent|lately|recently|past\s+few\s+days)',
            'tomorrow': r'\b(tomorrow|next\s+day)',
            'next_week': r'\b(next\s+week|coming\s+week)'
        }
        
        for context, pattern in time_patterns.items():
            if re.search(pattern, query):
                return context
        
        return None
    
    def _detect_urgency(self, query: str) -> str:
        """Detect urgency level from query"""
        urgent_keywords = ['urgent', 'asap', 'immediately', 'critical', 'emergency']
        high_keywords = ['important', 'priority', 'needed', 'quickly', 'soon']
        low_keywords = ['whenever', 'eventually', 'later', 'no rush']
        
        if any(keyword in query for keyword in urgent_keywords):
            return 'urgent'
        elif any(keyword in query for keyword in high_keywords):
            return 'high'
        elif any(keyword in query for keyword in low_keywords):
            return 'low'
        else:
            return 'normal'
    
    def _detect_scope(self, query: str) -> str:
        """Detect query scope"""
        if any(word in query for word in ['team', 'everyone', 'all', 'group']):
            return 'team'
        elif any(word in query for word in ['project', 'sprint', 'release']):
            return 'project'
        elif any(word in query for word in ['company', 'organization', 'org']):
            return 'organization'
        else:
            return 'personal'
    
    def _calculate_complexity(self, query: str, intent: Dict[str, Any]) -> float:
        """Calculate query complexity score (0.0 - 1.0)"""
        complexity = 0.0
        
        # Base complexity from query length
        word_count = len(query.split())
        complexity += min(word_count / 20, 0.3)  # Max 0.3 from length
        
        # Complexity from number of intents
        intent_count = 1 + len(intent.get('secondary_intents', []))
        complexity += min(intent_count / 5, 0.2)  # Max 0.2 from intents
        
        # Complexity from entities
        entity_count = len(intent.get('entities', []))
        complexity += min(entity_count / 10, 0.2)  # Max 0.2 from entities
        
        # Complexity from scope
        scope_complexity = {
            'personal': 0.1,
            'team': 0.2,
            'project': 0.3,
            'organization': 0.4
        }
        complexity += scope_complexity.get(intent.get('scope', 'team'), 0.2)
        
        return min(complexity, 1.0)
    
    def _determine_modules(self, intent: Dict[str, Any]) -> List[str]:
        """Determine which modules are needed for this query"""
        primary_intent = intent.get('primary_intent', 'general_query')
        modules = set()
        
        # Add modules for primary intent
        modules.update(self.intent_to_modules.get(primary_intent, ['team_comms_crawler']))
        
        # Add modules for secondary intents
        for secondary in intent.get('secondary_intents', []):
            modules.update(self.intent_to_modules.get(secondary, []))
        
        # Always include trust layer for confidence scoring
        modules.add('trust_layer')
        
        return list(modules)
    
    def _generate_processing_hints(
        self, 
        query: str, 
        intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate hints for query processing"""
        hints = {
            'parallel_processing': True,
            'cache_results': intent.get('urgency') in ['low', 'normal'],
            'time_sensitive': intent.get('time_context') is not None,
            'requires_aggregation': len(intent.get('secondary_intents', [])) > 0,
            'user_context_important': intent.get('scope') == 'personal'
        }
        
        # Add specific processing hints based on intent
        primary_intent = intent.get('primary_intent')
        
        if primary_intent == 'daily_brief':
            hints.update({
                'prioritize_recent': True,
                'summarize_content': True,
                'include_metrics': True
            })
        elif primary_intent == 'team_status':
            hints.update({
                'include_sentiment': True,
                'group_by_person': True,
                'highlight_blockers': True
            })
        elif primary_intent == 'project_status':
            hints.update({
                'include_progress_metrics': True,
                'highlight_milestones': True,
                'show_timeline': True
            })
        
        return hints
    
    def _create_fallback_parse(self, query: str) -> Dict[str, Any]:
        """Create fallback parsing for when primary parsing fails"""
        return {
            'original_query': query,
            'intent': {
                'primary_intent': 'general_query',
                'secondary_intents': [],
                'entities': [],
                'time_context': None,
                'urgency': 'normal',
                'scope': 'team',
                'query_type': 'question'
            },
            'complexity_score': 0.5,
            'confidence': 0.3,
            'modules_needed': ['team_comms_crawler', 'memory_engine'],
            'processing_hints': {
                'parallel_processing': True,
                'cache_results': True,
                'fallback_mode': True
            },
            'metadata': {
                'query_length': len(query),
                'word_count': len(query.split()),
                'fallback_used': True,
                'parsed_at': datetime.now(timezone.utc).isoformat()
            }
        }