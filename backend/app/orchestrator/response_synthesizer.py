"""
Response Synthesizer for Orchestrator
Combines and synthesizes responses from multiple modules into coherent intelligence
"""

from typing import Any, Dict, List, Optional, Tuple

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from langchain.output_parsers import PydanticOutputParser
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class SynthesizedResponse(BaseModel):
    """Structured synthesized response"""

    response: str = Field(description="Main synthesized response")
    confidence: float = Field(description="Overall confidence score 0.0-1.0")
    key_insights: List[str] = Field(default=[], description="Key insights extracted")
    action_items: List[str] = Field(default=[], description="Recommended actions")
    source_summary: str = Field(description="Summary of information sources")
    urgency_level: str = Field(default="normal", description="Response urgency")

@dataclass

class SynthesisContext:
    """Context for response synthesis"""

    query: str
    user_role: str = "team_lead"
    organization_context: Dict[str, Any] = field(default_factory=dict)
    time_context: Optional[str] = None
    urgency: str = "normal"
    preferred_style: str = "executive"  # executive, detailed, brief

class ResponseSynthesizer:
    """
    Advanced response synthesizer that combines information from multiple modules
    into coherent, actionable intelligence for team leads.

    Features:
    1. Multi-source data integration
    2. Confidence scoring and source attribution
    3. Executive-level summary generation
    4. Action item extraction
    5. Context-aware formatting
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.2,  # Slightly higher for more natural synthesis
            max_tokens=2000,
            request_timeout=60,
        )

        self.output_parser = PydanticOutputParser(pydantic_object=SynthesizedResponse)

        # Response templates by query type
        self.response_templates = {
            "daily_brief": self._get_daily_brief_template(),
            "team_status": self._get_team_status_template(),
            "project_update": self._get_project_update_template(),
            "ad_hoc_query": self._get_ad_hoc_template(),
            "memory_query": self._get_memory_template(),
            "integration_status": self._get_integration_template(),
        }

        logger.info("ResponseSynthesizer initialized")

    async def synthesize(
        self,
        query: str,
        module_results: Dict[str, Any],
        context: Any,
        synthesis_context: Optional[SynthesisContext] = None,
    ) -> Dict[str, Any]:
        """
        Synthesize responses from multiple modules into a coherent response.

        Args:
            query: Original user query
            module_results: Results from various modules
            context: Query context
            synthesis_context: Additional synthesis context

        Returns:
            Dictionary with synthesized response and metadata
        """
        try:
            logger.info(f"Synthesizing response for query: {query[:50]}...")

            # Prepare synthesis context
            if not synthesis_context:
                synthesis_context = SynthesisContext(query=query)

            # Analyze module results
            analysis = await self._analyze_module_results(module_results)

            # Determine synthesis strategy
            strategy = self._determine_synthesis_strategy(query, analysis, context)

            # Generate synthesized response
            synthesized = await self._generate_synthesis(
                query, module_results, analysis, strategy, synthesis_context
            )

            # Post-process and validate
            final_response = await self._post_process_response(
                synthesized, module_results, synthesis_context
            )

            return final_response

        except Exception as e:
            logger.error(f"Response synthesis failed: {e}")
            return self._create_fallback_response(query, module_results)

    async def _analyze_module_results(
        self, module_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze results from all modules to understand data quality and content"""
        analysis = {
            "data_quality": {},
            "content_themes": [],
            "confidence_scores": {},
            "source_diversity": 0,
            "data_freshness": "unknown",
            "completeness": 0.0,
        }

        total_sources = 0
        total_confidence = 0.0
        source_types = set()

        # Analyze each module's results
        for module_name, result in module_results.get("data", {}).items():
            if not result:
                continue

            # Count sources
            sources = result.get("sources", [])
            module_source_count = len(sources)
            total_sources += module_source_count

            # Track source diversity
            for source in sources:
                source_types.add(source.get("type", "unknown"))

            # Extract confidence if available
            if "confidence_metrics" in result.get("data", {}):
                confidence = result["data"]["confidence_metrics"].get(
                    "overall_confidence", 0.5
                )
                analysis["confidence_scores"][module_name] = confidence
                total_confidence += confidence

            # Analyze data quality
            analysis["data_quality"][module_name] = {
                "source_count": module_source_count,
                "has_metrics": "metrics" in result.get("data", {}),
                "has_recent_data": self._check_data_freshness(result),
                "completeness": min(
                    module_source_count / 5, 1.0
                ),  # Assume 5 sources is "complete"
            }

        # Calculate overall metrics
        module_count = len(analysis["confidence_scores"])
        if module_count > 0:
            analysis["confidence_scores"]["overall"] = total_confidence / module_count

        analysis["source_diversity"] = len(source_types)
        analysis["completeness"] = sum(
            qual["completeness"] for qual in analysis["data_quality"].values()
        ) / max(len(analysis["data_quality"]), 1)

        return analysis

    def _check_data_freshness(self, result: Dict[str, Any]) -> bool:
        """Check if module result contains recent data"""
        # Simple heuristic - look for timestamp indicators
        data = result.get("data", {})
        return any(
            "recent" in str(value).lower() or "today" in str(value).lower()
            for value in data.values()
            if isinstance(value, (str, list))
        )

    def _determine_synthesis_strategy(
        self, query: str, analysis: Dict[str, Any], context: Any
    ) -> Dict[str, Any]:
        """Determine the best strategy for synthesizing this response"""
        strategy = {
            "style": "executive",
            "focus": "balanced",
            "include_details": True,
            "prioritize_actions": False,
            "emphasize_confidence": False,
        }

        query_lower = query.lower()

        # Adjust style based on query type
        if any(word in query_lower for word in ["brief", "summary", "quick"]):
            strategy["style"] = "brief"
            strategy["include_details"] = False
        elif any(word in query_lower for word in ["detailed", "comprehensive", "full"]):
            strategy["style"] = "detailed"
            strategy["include_details"] = True

        # Adjust focus based on query intent
        if any(
            word in query_lower for word in ["action", "do", "next steps", "recommend"]
        ):
            strategy["focus"] = "actionable"
            strategy["prioritize_actions"] = True
        elif any(word in query_lower for word in ["status", "update", "progress"]):
            strategy["focus"] = "informational"

        # Emphasize confidence for uncertain data
        overall_confidence = analysis.get("confidence_scores", {}).get("overall", 0.5)
        if overall_confidence < 0.7:
            strategy["emphasize_confidence"] = True

        return strategy

    async def _generate_synthesis(
        self,
        query: str,
        module_results: Dict[str, Any],
        analysis: Dict[str, Any],
        strategy: Dict[str, Any],
        synthesis_context: SynthesisContext,
    ) -> Dict[str, Any]:
        """Generate the main synthesized response using LLM"""

        # Prepare data summary for LLM
        data_summary = self._prepare_data_summary(module_results)

        # Get appropriate system prompt
        system_prompt = self._get_synthesis_prompt(strategy, synthesis_context)

        # Prepare user message
        user_message = f"""
Query: "{query}"

Module Data Summary:
{data_summary}

Data Quality Analysis:
- Overall Confidence: {analysis.get('confidence_scores', {}).get('overall', 0.5):.2f}
- Source Diversity: {analysis.get('source_diversity', 0)} different types
- Data Completeness: {analysis.get('completeness', 0.0):.1%}

Please synthesize this information into a coherent response following the specified format.
"""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message),
            ]

            response = await self.llm.ainvoke(messages)

            # Parse structured response
            try:
                parsed_response = self.output_parser.parse(response.content)
                return {
                    "response": parsed_response.response,
                    "confidence": parsed_response.confidence,
                    "key_insights": parsed_response.key_insights,
                    "action_items": parsed_response.action_items,
                    "source_summary": parsed_response.source_summary,
                    "urgency_level": parsed_response.urgency_level,
                    "metadata": {
                        "synthesis_strategy": strategy,
                        "data_analysis": analysis,
                        "synthesis_timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                }
            except Exception as parse_error:
                logger.warning(f"Failed to parse structured response: {parse_error}")
                # Fallback to unstructured response
                return self._create_unstructured_response(response.content, analysis)

        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}")
            raise

    def _prepare_data_summary(self, module_results: Dict[str, Any]) -> str:
        """Prepare a concise summary of module data for LLM processing"""
        summary_parts = []

        for module_name, result in module_results.get("data", {}).items():
            if not result:
                continue

            sources = result.get("sources", [])
            data = result.get("data", {})

            module_summary = f"\n{module_name.replace('_', ' ').title()}:"

            # Add source information
            if sources:
                source_count = len(sources)
                source_types = list(
                    set(source.get("type", "unknown") for source in sources)
                )
                module_summary += f"\n  Sources: {source_count} sources from {', '.join(source_types)}"

            # Add key data points
            if data:
                key_points = []
                for key, value in data.items():
                    if isinstance(value, list) and value:
                        key_points.append(f"{key}: {len(value)} items")
                    elif isinstance(value, dict) and value:
                        key_points.append(f"{key}: {len(value)} entries")
                    elif isinstance(value, str) and len(value) < 100:
                        key_points.append(f"{key}: {value}")

                if key_points:
                    module_summary += (
                        f"\n  Data: {'; '.join(key_points[:3])}"  # Limit to top 3
                    )

            summary_parts.append(module_summary)

        # Add error information if any
        errors = module_results.get("errors", [])
        if errors:
            error_summary = f"\nErrors encountered: {len(errors)} modules failed"
            summary_parts.append(error_summary)

        return "\n".join(summary_parts)

    def _get_synthesis_prompt(
        self, strategy: Dict[str, Any], synthesis_context: SynthesisContext
    ) -> str:
        """Get the appropriate system prompt for synthesis"""

        base_prompt = f"""
You are an expert intelligence synthesizer for SingleBrief, helping team leads and managers
get actionable insights from their team and organizational data.

Your role is to:
1. Synthesize information from multiple data sources into coherent intelligence
2. Provide executive-level insights that are immediately actionable
3. Maintain appropriate confidence levels and cite sources
4. Format responses for busy managers who need quick, accurate information

Context:
- User Role: {synthesis_context.user_role}
- Communication Style: {synthesis_context.preferred_style}
- Urgency: {synthesis_context.urgency}

{self.output_parser.get_format_instructions()}

Key principles:
- Be concise but comprehensive
- Lead with the most important information
- Always indicate confidence levels
- Provide specific, actionable recommendations when appropriate
- Cite sources and explain any limitations in the data
"""

        # Add style-specific guidance
        if strategy["style"] == "brief":
            base_prompt += "\n- Keep response under 200 words, focus on key points only"
        elif strategy["style"] == "detailed":
            base_prompt += "\n- Provide comprehensive analysis with supporting details"

        if strategy["prioritize_actions"]:
            base_prompt += "\n- Emphasize actionable recommendations and next steps"

        if strategy["emphasize_confidence"]:
            base_prompt += (
                "\n- Clearly communicate confidence levels and data limitations"
            )

        return base_prompt

    async def _post_process_response(
        self,
        synthesized: Dict[str, Any],
        module_results: Dict[str, Any],
        synthesis_context: SynthesisContext,
    ) -> Dict[str, Any]:
        """Post-process the synthesized response for final delivery"""

        # Enhance source attribution
        sources = []
        for module_name, result in module_results.get("data", {}).items():
            module_sources = result.get("sources", [])
            for source in module_sources:
                sources.append(
                    {
                        "module": module_name,
                        "type": source.get("type"),
                        "name": source.get("name"),
                        "details": source,
                    }
                )

        # Calculate final confidence score
        confidence_factors = [
            synthesized.get("confidence", 0.5),
            min(len(sources) / 5, 1.0),  # Source diversity factor
            module_results.get("data_quality_score", 0.7),  # Data quality factor
        ]
        final_confidence = sum(confidence_factors) / len(confidence_factors)

        # Format final response
        final_response = {
            "response": synthesized["response"],
            "confidence": round(final_confidence, 2),
            "key_insights": synthesized.get("key_insights", []),
            "action_items": synthesized.get("action_items", []),
            "sources": sources,
            "source_summary": synthesized.get("source_summary", ""),
            "urgency_level": synthesized.get("urgency_level", "normal"),
            "metadata": synthesized.get("metadata", {}),
            "synthesis_timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return final_response

    def _create_unstructured_response(
        self, content: str, analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create response when structured parsing fails"""
        return {
            "response": content,
            "confidence": analysis.get("confidence_scores", {}).get("overall", 0.5),
            "key_insights": [],
            "action_items": [],
            "source_summary": f"Synthesized from {len(analysis.get('data_quality', {}))} modules",
            "urgency_level": "normal",
            "metadata": {
                "fallback_used": True,
                "synthesis_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

    def _create_fallback_response(
        self, query: str, module_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create fallback response when synthesis completely fails"""

        # Extract basic information from module results
        total_sources = sum(
            len(result.get("sources", []))
            for result in module_results.get("data", {}).values()
        )

        module_count = len(module_results.get("data", {}))
        error_count = len(module_results.get("errors", []))

        fallback_text = f"""
I've gathered information from {module_count} data sources to answer your query,
but encountered some processing challenges. Here's what I can tell you:

Based on {total_sources} data points from your connected systems, I have information
available but need to present it in a simplified format due to technical constraints.
"""

        if error_count > 0:
            fallback_text += (
                f"\n\nNote: {error_count} data sources were temporarily unavailable."
            )

        return {
            "response": fallback_text.strip(),
            "confidence": 0.3,
            "key_insights": [],
            "action_items": [
                "Please try your query again for a more detailed response"
            ],
            "source_summary": f"Data from {module_count} modules, {total_sources} sources",
            "urgency_level": "normal",
            "metadata": {
                "fallback_response": True,
                "synthesis_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

    # Template methods for different response types
    def _get_daily_brief_template(self) -> str:
        return "Focus on recent activities, key metrics, and priority items for today."

    def _get_team_status_template(self) -> str:
        return "Highlight team member activities, blockers, and overall team health."

    def _get_project_update_template(self) -> str:
        return "Emphasize project progress, milestones, and potential risks or delays."

    def _get_ad_hoc_template(self) -> str:
        return "Provide direct, comprehensive answer to the specific question asked."

    def _get_memory_template(self) -> str:
        return "Present relevant historical context and learned patterns."

    def _get_integration_template(self) -> str:
        return "Focus on system status, data flow health, and integration performance."
