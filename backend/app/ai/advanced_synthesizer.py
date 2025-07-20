"""
Advanced Synthesizer Engine for Multi-Source Data
Enhanced synthesis capabilities with contradiction detection and source attribution
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from app.ai.llm_integration import LLMManager, QueryType
from app.ai.rag_pipeline import DocumentType, RetrievedContext

logger = logging.getLogger(__name__)

class SynthesisStrategy(str, Enum):
    """Different synthesis strategies"""

    HIERARCHICAL = "hierarchical"
    TEMPORAL = "temporal"
    SOURCE_WEIGHTED = "source_weighted"
    CONSENSUS = "consensus"
    EXPERT_PRIORITY = "expert_priority"

class ContradictionType(str, Enum):
    """Types of contradictions found in data"""

    FACTUAL = "factual"
    TEMPORAL = "temporal"
    OPINION = "opinion"
    MEASUREMENT = "measurement"
    STATUS = "status"

class SourceReliability(str, Enum):
    """Source reliability levels"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"

@dataclass

class DataPoint:
    """Individual piece of information with metadata"""

    content: str
    source: str
    document_type: DocumentType
    timestamp: Optional[datetime]
    reliability: SourceReliability
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    fingerprint: str = field(init=False)

    def __post_init__(self):
        self.fingerprint = hashlib.md5(self.content.encode()).hexdigest()

@dataclass

class Contradiction:
    """Detected contradiction between data points"""

    contradiction_type: ContradictionType
    conflicting_points: List[DataPoint]
    severity: float  # 0.0 to 1.0
    explanation: str
    resolution_strategy: str
    confidence: float

@dataclass

class SynthesizedInformation:
    """Synthesized information with full provenance"""

    synthesized_content: str
    source_data_points: List[DataPoint]
    contradictions_found: List[Contradiction]
    synthesis_strategy: SynthesisStrategy
    confidence_score: float
    temporal_context: Optional[str]
    key_insights: List[str]
    source_attribution: Dict[str, List[str]]
    processing_metadata: Dict[str, Any]

class SourceAnalyzer:
    """Analyzes and scores source reliability and content quality"""

    def __init__(self):
        self.source_patterns = {
            # Official/authoritative sources
            "official": {
                "patterns": ["official", "documentation", "policy", "announcement"],
                "base_reliability": SourceReliability.HIGH,
                "confidence_boost": 0.2,
            },
            # Team leads and managers
            "leadership": {
                "patterns": ["manager", "lead", "director", "vp", "ceo"],
                "base_reliability": SourceReliability.HIGH,
                "confidence_boost": 0.15,
            },
            # Recent communications
            "recent": {
                "patterns": ["today", "yesterday", "this week", "recent"],
                "base_reliability": SourceReliability.MEDIUM,
                "confidence_boost": 0.1,
            },
            # Meeting notes and decisions
            "formal": {
                "patterns": ["meeting", "decision", "resolution", "minutes"],
                "base_reliability": SourceReliability.MEDIUM,
                "confidence_boost": 0.1,
            },
        }

    def analyze_source(self, data_point: DataPoint) -> Tuple[SourceReliability, float]:
        """Analyze source reliability and confidence"""

        base_reliability = SourceReliability.MEDIUM
        confidence_boost = 0.0

        content_lower = data_point.content.lower()
        source_lower = data_point.source.lower()

        # Analyze content and source for reliability indicators
        for category, config in self.source_patterns.items():
            for pattern in config["patterns"]:
                if pattern in content_lower or pattern in source_lower:
                    if config["base_reliability"].value == "high":
                        base_reliability = SourceReliability.HIGH
                    confidence_boost = max(confidence_boost, config["confidence_boost"])
                    break

        # Adjust confidence based on content characteristics
        content_confidence = self._analyze_content_confidence(data_point.content)
        final_confidence = min(
            data_point.confidence + confidence_boost + content_confidence, 1.0
        )

        return base_reliability, final_confidence

    def _analyze_content_confidence(self, content: str) -> float:
        """Analyze content characteristics for confidence scoring"""

        confidence_boost = 0.0

        # Longer, more detailed content tends to be more reliable
        if len(content) > 200:
            confidence_boost += 0.05

        # Specific numbers and dates indicate concrete information
        import re

        if re.search(r"\b\d{1,2}/\d{1,2}/\d{4}\b", content):  # Dates
            confidence_boost += 0.05
        if re.search(r"\b\d+%\b", content):  # Percentages
            confidence_boost += 0.05

        # Hedge words reduce confidence
        hedge_words = ["maybe", "perhaps", "might", "could", "possibly", "probably"]
        hedge_count = sum(1 for word in hedge_words if word in content.lower())
        confidence_boost -= hedge_count * 0.02

        return max(confidence_boost, -0.1)  # Don't reduce too much

class ContradictionDetector:
    """Detects and analyzes contradictions in multi-source data"""

    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager

        # Patterns that indicate potential contradictions
        self.contradiction_patterns = {
            ContradictionType.TEMPORAL: [
                "before",
                "after",
                "earlier",
                "later",
                "previous",
                "next",
            ],
            ContradictionType.STATUS: [
                "completed",
                "in progress",
                "pending",
                "cancelled",
                "delayed",
            ],
            ContradictionType.MEASUREMENT: [
                "increase",
                "decrease",
                "higher",
                "lower",
                "more",
                "less",
            ],
            ContradictionType.FACTUAL: [
                "yes",
                "no",
                "true",
                "false",
                "confirmed",
                "denied",
            ],
        }

    async def detect_contradictions(
        self, data_points: List[DataPoint]
    ) -> List[Contradiction]:
        """Detect contradictions between data points"""

        contradictions = []

        # Group data points by similarity for comparison
        similar_groups = self._group_similar_content(data_points)

        for group in similar_groups:
            if len(group) > 1:
                group_contradictions = await self._analyze_group_contradictions(group)
                contradictions.extend(group_contradictions)

        return contradictions

    def _group_similar_content(
        self, data_points: List[DataPoint]
    ) -> List[List[DataPoint]]:
        """Group data points with similar content"""

        groups = []
        processed = set()

        for i, dp1 in enumerate(data_points):
            if dp1.fingerprint in processed:
                continue

            group = [dp1]
            processed.add(dp1.fingerprint)

            for j, dp2 in enumerate(data_points[i + 1 :], i + 1):
                if dp2.fingerprint in processed:
                    continue

                # Simple similarity check - can be enhanced
                similarity = self._calculate_content_similarity(
                    dp1.content, dp2.content
                )
                if similarity > 0.3:  # Threshold for grouping
                    group.append(dp2)
                    processed.add(dp2.fingerprint)

            if len(group) > 1:
                groups.append(group)

        return groups

    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate simple content similarity"""

        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    async def _analyze_group_contradictions(
        self, group: List[DataPoint]
    ) -> List[Contradiction]:
        """Analyze a group of similar data points for contradictions"""

        contradictions = []

        # Use LLM to detect semantic contradictions
        content_summary = "\n".join(
            [
                f"Source {i+1} ({dp.source}): {dp.content[:200]}..."
                for i, dp in enumerate(group)
            ]
        )

        prompt = f"""
        Analyze these related pieces of information for contradictions:

        {content_summary}

        Identify any contradictions and classify them as:
        - FACTUAL: Conflicting facts or statements
        - TEMPORAL: Conflicting timing or sequence
        - STATUS: Conflicting status reports
        - MEASUREMENT: Conflicting numbers or measurements
        - OPINION: Conflicting opinions or interpretations

        For each contradiction found, provide:
        1. Type of contradiction
        2. Which sources conflict
        3. Severity (1-10)
        4. Brief explanation
        5. Suggested resolution approach
        """

        try:
            response = await self.llm_manager.generate_response(
                prompt,
                QueryType.ANALYSIS,
                system_message="You are an expert at detecting contradictions in information.",
            )

            # Parse contradictions from response
            parsed_contradictions = self._parse_contradiction_response(
                response.content, group
            )
            contradictions.extend(parsed_contradictions)

        except Exception as e:
            logger.error(f"LLM contradiction analysis failed: {e}")

        return contradictions

    def _parse_contradiction_response(
        self, response: str, group: List[DataPoint]
    ) -> List[Contradiction]:
        """Parse contradiction analysis response from LLM"""

        contradictions = []

        # Simple parsing - can be enhanced with structured output
        lines = response.split("\n")

        current_contradiction = {}
        for line in lines:
            line = line.strip()

            if any(ct.value.upper() in line.upper() for ct in ContradictionType):
                if current_contradiction:
                    # Process previous contradiction
                    contradiction = self._create_contradiction_from_parsed(
                        current_contradiction, group
                    )
                    if contradiction:
                        contradictions.append(contradiction)

                # Start new contradiction
                current_contradiction = {"type_line": line}

            elif line and current_contradiction:
                if "explanation" not in current_contradiction:
                    current_contradiction["explanation"] = line
                elif "resolution" not in current_contradiction:
                    current_contradiction["resolution"] = line

        # Process last contradiction
        if current_contradiction:
            contradiction = self._create_contradiction_from_parsed(
                current_contradiction, group
            )
            if contradiction:
                contradictions.append(contradiction)

        return contradictions

    def _create_contradiction_from_parsed(
        self, parsed: Dict[str, str], group: List[DataPoint]
    ) -> Optional[Contradiction]:
        """Create Contradiction object from parsed data"""

        try:
            # Extract contradiction type
            type_line = parsed.get("type_line", "").upper()
            contradiction_type = ContradictionType.FACTUAL  # Default

            for ct in ContradictionType:
                if ct.value.upper() in type_line:
                    contradiction_type = ct
                    break

            # Extract severity (look for numbers 1-10)
            import re

            severity_match = re.search(r"\b([1-9]|10)\b", parsed.get("explanation", ""))
            severity = float(severity_match.group(1)) / 10 if severity_match else 0.5

            return Contradiction(
                contradiction_type=contradiction_type,
                conflicting_points=group,
                severity=severity,
                explanation=parsed.get("explanation", "Contradiction detected"),
                resolution_strategy=parsed.get("resolution", "Manual review required"),
                confidence=0.7,  # LLM-based detection confidence
            )

        except Exception as e:
            logger.error(f"Failed to create contradiction: {e}")
            return None

class AdvancedSynthesizer:
    """
    Advanced multi-source data synthesizer with contradiction detection.

    Features:
    1. Multi-source data aggregation and deduplication
    2. Contradiction detection and resolution
    3. Source reliability assessment
    4. Temporal information handling
    5. Context-aware synthesis strategies
    6. Comprehensive source attribution
    """

    def __init__(self):
        self.llm_manager = LLMManager()
        self.source_analyzer = SourceAnalyzer()
        self.contradiction_detector = ContradictionDetector(self.llm_manager)

        # Synthesis templates for different strategies
        self.synthesis_templates = {
            SynthesisStrategy.HIERARCHICAL: self._get_hierarchical_template(),
            SynthesisStrategy.TEMPORAL: self._get_temporal_template(),
            SynthesisStrategy.SOURCE_WEIGHTED: self._get_source_weighted_template(),
            SynthesisStrategy.CONSENSUS: self._get_consensus_template(),
            SynthesisStrategy.EXPERT_PRIORITY: self._get_expert_priority_template(),
        }

        logger.info("Advanced Synthesizer initialized")

    async def synthesize_information(
        self,
        contexts: List[RetrievedContext],
        query: str,
        synthesis_strategy: SynthesisStrategy = SynthesisStrategy.SOURCE_WEIGHTED,
        include_contradictions: bool = True,
        temporal_focus: Optional[str] = None,
    ) -> SynthesizedInformation:
        """
        Synthesize information from multiple sources with contradiction handling.

        Args:
            contexts: Retrieved contexts from RAG pipeline
            query: Original query for context
            synthesis_strategy: Strategy to use for synthesis
            include_contradictions: Whether to detect and include contradictions
            temporal_focus: Time period to focus on (e.g., "recent", "this week")

        Returns:
            SynthesizedInformation with comprehensive synthesis
        """

        try:
            # Convert contexts to data points
            data_points = await self._convert_contexts_to_datapoints(contexts)

            # Analyze source reliability
            for dp in data_points:
                reliability, confidence = self.source_analyzer.analyze_source(dp)
                dp.reliability = reliability
                dp.confidence = confidence

            # Detect contradictions if requested
            contradictions = []
            if include_contradictions and len(data_points) > 1:
                contradictions = (
                    await self.contradiction_detector.detect_contradictions(data_points)
                )

            # Apply synthesis strategy
            synthesized_content = await self._apply_synthesis_strategy(
                data_points, query, synthesis_strategy, temporal_focus
            )

            # Extract key insights
            key_insights = await self._extract_key_insights(
                synthesized_content, data_points
            )

            # Generate source attribution
            source_attribution = self._generate_source_attribution(data_points)

            # Calculate overall confidence
            confidence_score = self._calculate_synthesis_confidence(
                data_points, contradictions
            )

            return SynthesizedInformation(
                synthesized_content=synthesized_content,
                source_data_points=data_points,
                contradictions_found=contradictions,
                synthesis_strategy=synthesis_strategy,
                confidence_score=confidence_score,
                temporal_context=temporal_focus,
                key_insights=key_insights,
                source_attribution=source_attribution,
                processing_metadata={
                    "total_sources": len(data_points),
                    "contradiction_count": len(contradictions),
                    "average_source_confidence": (
                        sum(dp.confidence for dp in data_points) / len(data_points)
                        if data_points
                        else 0.0
                    ),
                    "synthesis_timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

        except Exception as e:
            logger.error(f"Information synthesis failed: {e}")
            raise

    async def _convert_contexts_to_datapoints(
        self, contexts: List[RetrievedContext]
    ) -> List[DataPoint]:
        """Convert retrieved contexts to data points for analysis"""

        data_points = []

        for context in contexts:
            # Extract timestamp from metadata if available
            timestamp = None
            if "timestamp" in context.metadata:
                try:
                    timestamp = datetime.fromisoformat(context.metadata["timestamp"])
                except (ValueError, KeyError, TypeError):
                    pass

            data_point = DataPoint(
                content=context.content,
                source=context.source,
                document_type=context.document_type,
                timestamp=timestamp,
                reliability=SourceReliability.UNKNOWN,  # Will be analyzed
                confidence=context.relevance_score,
                metadata=context.metadata,
            )

            data_points.append(data_point)

        return data_points

    async def _apply_synthesis_strategy(
        self,
        data_points: List[DataPoint],
        query: str,
        strategy: SynthesisStrategy,
        temporal_focus: Optional[str],
    ) -> str:
        """Apply the selected synthesis strategy"""

        # Prepare data for synthesis
        if strategy == SynthesisStrategy.TEMPORAL and temporal_focus:
            data_points = self._filter_by_temporal_focus(data_points, temporal_focus)
        elif strategy == SynthesisStrategy.SOURCE_WEIGHTED:
            data_points = self._weight_by_source_reliability(data_points)
        elif strategy == SynthesisStrategy.EXPERT_PRIORITY:
            data_points = self._prioritize_expert_sources(data_points)

        # Get synthesis template
        template = self.synthesis_templates.get(
            strategy, self.synthesis_templates[SynthesisStrategy.SOURCE_WEIGHTED]
        )

        # Prepare content for LLM
        content_summary = self._prepare_content_for_synthesis(data_points, strategy)

        # Generate synthesis prompt
        synthesis_prompt = template.format(
            query=query,
            content=content_summary,
            temporal_focus=temporal_focus or "all available timeframes",
        )

        # Generate synthesized response
        response = await self.llm_manager.generate_response(
            synthesis_prompt,
            QueryType.SYNTHESIS,
            system_message="You are an expert at synthesizing information from multiple sources.",
        )

        return response.content

    def _filter_by_temporal_focus(
        self, data_points: List[DataPoint], temporal_focus: str
    ) -> List[DataPoint]:
        """Filter data points based on temporal focus"""

        if temporal_focus.lower() in ["recent", "latest", "current"]:
            # Sort by timestamp and take most recent
            timestamped_points = [dp for dp in data_points if dp.timestamp]
            if timestamped_points:
                timestamped_points.sort(key=lambda x: x.timestamp, reverse=True)
                return timestamped_points[
                    : len(data_points) // 2
                ]  # Top half by recency

        return data_points

    def _weight_by_source_reliability(
        self, data_points: List[DataPoint]
    ) -> List[DataPoint]:
        """Weight data points by source reliability"""

        # Sort by reliability and confidence
        weighted_points = sorted(
            data_points,
            key=lambda x: (x.reliability.value == "high", x.confidence),
            reverse=True,
        )

        return weighted_points

    def _prioritize_expert_sources(
        self, data_points: List[DataPoint]
    ) -> List[DataPoint]:
        """Prioritize expert and authoritative sources"""

        expert_indicators = [
            "manager",
            "lead",
            "director",
            "expert",
            "official",
            "documentation",
        ]

        def is_expert_source(dp: DataPoint) -> bool:
            source_lower = dp.source.lower()
            content_lower = dp.content.lower()
            return any(
                indicator in source_lower or indicator in content_lower
                for indicator in expert_indicators
            )

        expert_points = [dp for dp in data_points if is_expert_source(dp)]
        other_points = [dp for dp in data_points if not is_expert_source(dp)]

        return expert_points + other_points

    def _prepare_content_for_synthesis(
        self, data_points: List[DataPoint], strategy: SynthesisStrategy
    ) -> str:
        """Prepare content summary for synthesis"""

        content_parts = []

        for i, dp in enumerate(data_points, 1):
            reliability_indicator = (
                "🟢"
                if dp.reliability == SourceReliability.HIGH
                else "🟡" if dp.reliability == SourceReliability.MEDIUM else "🔴"
            )

            content_part = f"""
Source {i} {reliability_indicator} ({dp.source}) - Confidence: {dp.confidence:.2f}
Type: {dp.document_type.value}
{f"Timestamp: {dp.timestamp.strftime('%Y-%m-%d %H:%M')}" if dp.timestamp else ""}
Content: {dp.content}
"""
            content_parts.append(content_part.strip())

        return "\n\n---\n\n".join(content_parts)

    async def _extract_key_insights(
        self, synthesized_content: str, data_points: List[DataPoint]
    ) -> List[str]:
        """Extract key insights from synthesized content"""

        prompt = f"""
        From this synthesized information, extract the top 3-5 key insights that would be most valuable for a team lead:

        {synthesized_content}

        Format as a numbered list of concise insights.
        """

        try:
            response = await self.llm_manager.generate_response(
                prompt,
                QueryType.ANALYSIS,
                system_message="Extract key insights for leadership decision-making.",
            )

            # Parse insights from response
            insights = []
            lines = response.content.split("\n")

            for line in lines:
                line = line.strip()
                if line and any(line.startswith(str(i)) for i in range(1, 10)):
                    insight = line.split(".", 1)[-1].strip()
                    if insight:
                        insights.append(insight)

            return insights

        except Exception as e:
            logger.error(f"Key insight extraction failed: {e}")
            return []

    def _generate_source_attribution(
        self, data_points: List[DataPoint]
    ) -> Dict[str, List[str]]:
        """Generate comprehensive source attribution"""

        attribution = {
            "sources": [],
            "document_types": [],
            "reliability_breakdown": {"high": [], "medium": [], "low": []},
        }

        for dp in data_points:
            if dp.source not in attribution["sources"]:
                attribution["sources"].append(dp.source)

            if dp.document_type.value not in attribution["document_types"]:
                attribution["document_types"].append(dp.document_type.value)

            if (
                dp.source
                not in attribution["reliability_breakdown"][dp.reliability.value]
            ):
                attribution["reliability_breakdown"][dp.reliability.value].append(
                    dp.source
                )

        return attribution

    def _calculate_synthesis_confidence(
        self, data_points: List[DataPoint], contradictions: List[Contradiction]
    ) -> float:
        """Calculate overall confidence in the synthesis"""

        if not data_points:
            return 0.0

        # Base confidence on average source confidence
        avg_confidence = sum(dp.confidence for dp in data_points) / len(data_points)

        # Adjust for source reliability
        high_reliability_count = sum(
            1 for dp in data_points if dp.reliability == SourceReliability.HIGH
        )
        reliability_boost = (high_reliability_count / len(data_points)) * 0.1

        # Reduce confidence for contradictions
        contradiction_penalty = len(contradictions) * 0.05

        # Consider source diversity
        unique_sources = len(set(dp.source for dp in data_points))
        diversity_boost = min(
            unique_sources / 5, 0.1
        )  # Up to 10% boost for diverse sources

        final_confidence = (
            avg_confidence + reliability_boost + diversity_boost - contradiction_penalty
        )
        return max(0.0, min(1.0, final_confidence))

    # Synthesis templates
    def _get_hierarchical_template(self) -> str:
        return """
        Synthesize the following information using a hierarchical approach, prioritizing official and authoritative sources:

        Query: {query}
        Temporal Focus: {temporal_focus}

        Information Sources:
        {content}

        Create a comprehensive response that:
        1. Prioritizes information from the most reliable sources
        2. Structures information hierarchically by importance
        3. Clearly indicates the authority level of each piece of information
        4. Provides a clear, actionable summary
        """

    def _get_temporal_template(self) -> str:
        return """
        Synthesize the following information with a focus on temporal context and chronology:

        Query: {query}
        Temporal Focus: {temporal_focus}

        Information Sources:
        {content}

        Create a response that:
        1. Organizes information chronologically
        2. Highlights the most recent and relevant information
        3. Shows how information has evolved over time
        4. Emphasizes current status and recent changes
        """

    def _get_source_weighted_template(self) -> str:
        return """
        Synthesize the following information by weighting sources based on their reliability and confidence scores:

        Query: {query}
        Temporal Focus: {temporal_focus}

        Information Sources:
        {content}

        Create a balanced response that:
        1. Gives appropriate weight to each source based on reliability indicators
        2. Integrates information proportionally to source confidence
        3. Notes any uncertainty or conflicting information
        4. Provides a well-balanced, comprehensive answer
        """

    def _get_consensus_template(self) -> str:
        return """
        Synthesize the following information by identifying consensus and common themes:

        Query: {query}
        Temporal Focus: {temporal_focus}

        Information Sources:
        {content}

        Create a response that:
        1. Identifies points of consensus across sources
        2. Highlights common themes and patterns
        3. Notes areas of agreement and disagreement
        4. Provides a consensus-based summary where possible
        """

    def _get_expert_priority_template(self) -> str:
        return """
        Synthesize the following information by prioritizing expert and authoritative voices:

        Query: {query}
        Temporal Focus: {temporal_focus}

        Information Sources:
        {content}

        Create a response that:
        1. Prioritizes insights from experts and leaders
        2. Uses authoritative sources as the foundation
        3. Supplements with supporting information from other sources
        4. Clearly distinguishes expert opinions from general information
        """
