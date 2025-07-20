"""
Trust Layer and Confidence Scoring System
Advanced trust assessment and transparency for AI-generated intelligence
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
import hashlib
import statistics

from app.ai.llm_integration import LLMManager, QueryType

logger = logging.getLogger(__name__)


class TrustLevel(str, Enum):
    """Trust levels for information and sources"""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


class ConfidenceCategory(str, Enum):
    """Categories for confidence assessment"""
    FACTUAL_ACCURACY = "factual_accuracy"
    SOURCE_RELIABILITY = "source_reliability"
    DATA_FRESHNESS = "data_freshness"
    CROSS_VALIDATION = "cross_validation"
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"


class ValidationMethod(str, Enum):
    """Methods used for validation"""
    CROSS_REFERENCE = "cross_reference"
    TEMPORAL_CONSISTENCY = "temporal_consistency"
    SOURCE_AUTHORITY = "source_authority"
    PEER_CONSENSUS = "peer_consensus"
    EXPERT_VERIFICATION = "expert_verification"
    AUTOMATED_FACT_CHECK = "automated_fact_check"


@dataclass
class ConfidenceMetric:
    """Individual confidence metric with details"""
    category: ConfidenceCategory
    score: float  # 0.0 to 1.0
    method: ValidationMethod
    explanation: str
    evidence_count: int
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class TrustAssessment:
    """Comprehensive trust assessment for information"""
    overall_confidence: float
    trust_level: TrustLevel
    confidence_metrics: Dict[ConfidenceCategory, ConfidenceMetric]
    validation_methods: List[ValidationMethod]
    trust_indicators: List[str]
    risk_factors: List[str]
    source_credibility_scores: Dict[str, float]
    temporal_reliability: float
    cross_validation_score: float
    assessment_metadata: Dict[str, Any]


@dataclass
class SourceCredibilityProfile:
    """Credibility profile for information sources"""
    source_id: str
    source_name: str
    authority_level: float
    historical_accuracy: float
    consistency_score: float
    expertise_domains: List[str]
    last_verified: datetime
    verification_count: int
    feedback_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class SourceCredibilityTracker:
    """Tracks and manages source credibility over time"""
    
    def __init__(self):
        self.source_profiles: Dict[str, SourceCredibilityProfile] = {}
        self.domain_experts: Dict[str, List[str]] = {}  # domain -> list of expert source_ids
        
        # Authority indicators
        self.authority_indicators = {
            'official': 0.9,
            'documentation': 0.85,
            'leadership': 0.8,
            'expert': 0.75,
            'team_lead': 0.7,
            'verified': 0.65,
            'internal': 0.6,
            'community': 0.4,
            'unverified': 0.2
        }
        
        logger.info("Source Credibility Tracker initialized")
    
    def get_or_create_profile(self, source_id: str, source_name: str) -> SourceCredibilityProfile:
        """Get existing profile or create new one for source"""
        
        if source_id not in self.source_profiles:
            # Analyze source name for authority indicators
            authority_level = self._calculate_initial_authority(source_name)
            
            self.source_profiles[source_id] = SourceCredibilityProfile(
                source_id=source_id,
                source_name=source_name,
                authority_level=authority_level,
                historical_accuracy=0.5,  # Neutral starting point
                consistency_score=0.5,
                expertise_domains=[],
                last_verified=datetime.now(timezone.utc),
                verification_count=0,
                feedback_score=0.5
            )
        
        return self.source_profiles[source_id]
    
    def _calculate_initial_authority(self, source_name: str) -> float:
        """Calculate initial authority level based on source name"""
        
        source_lower = source_name.lower()
        max_authority = 0.0
        
        for indicator, authority in self.authority_indicators.items():
            if indicator in source_lower:
                max_authority = max(max_authority, authority)
        
        return max_authority if max_authority > 0.0 else 0.3  # Default authority
    
    def update_source_accuracy(self, source_id: str, accuracy_score: float):
        """Update historical accuracy for a source"""
        
        if source_id in self.source_profiles:
            profile = self.source_profiles[source_id]
            
            # Use exponential moving average
            alpha = 0.3  # Learning rate
            profile.historical_accuracy = (
                alpha * accuracy_score + 
                (1 - alpha) * profile.historical_accuracy
            )
            
            profile.verification_count += 1
            profile.last_verified = datetime.now(timezone.utc)
    
    def update_source_consistency(self, source_id: str, consistency_score: float):
        """Update consistency score for a source"""
        
        if source_id in self.source_profiles:
            profile = self.source_profiles[source_id]
            
            alpha = 0.3
            profile.consistency_score = (
                alpha * consistency_score + 
                (1 - alpha) * profile.consistency_score
            )
    
    def add_expertise_domain(self, source_id: str, domain: str):
        """Add expertise domain for a source"""
        
        if source_id in self.source_profiles:
            profile = self.source_profiles[source_id]
            if domain not in profile.expertise_domains:
                profile.expertise_domains.append(domain)
            
            # Update domain experts mapping
            if domain not in self.domain_experts:
                self.domain_experts[domain] = []
            if source_id not in self.domain_experts[domain]:
                self.domain_experts[domain].append(source_id)
    
    def get_domain_experts(self, domain: str) -> List[SourceCredibilityProfile]:
        """Get expert sources for a specific domain"""
        
        expert_ids = self.domain_experts.get(domain, [])
        return [self.source_profiles[sid] for sid in expert_ids if sid in self.source_profiles]
    
    def calculate_source_credibility(self, source_id: str) -> float:
        """Calculate overall credibility score for a source"""
        
        if source_id not in self.source_profiles:
            return 0.3  # Default low credibility
        
        profile = self.source_profiles[source_id]
        
        # Weighted combination of factors
        credibility = (
            profile.authority_level * 0.4 +
            profile.historical_accuracy * 0.3 +
            profile.consistency_score * 0.2 +
            min(profile.feedback_score, 1.0) * 0.1
        )
        
        # Boost for verified sources
        if profile.verification_count > 5:
            credibility += 0.05
        
        # Penalty for stale sources
        days_since_verified = (datetime.now(timezone.utc) - profile.last_verified).days
        if days_since_verified > 30:
            credibility -= 0.1
        
        return max(0.0, min(1.0, credibility))


class FactChecker:
    """Automated fact checking and validation"""
    
    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager
        
        # Known fact patterns
        self.fact_patterns = {
            'numerical': r'\b\d+(\.\d+)?%?\b',
            'dates': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            'names': r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            'urls': r'https?://[^\s]+',
            'emails': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        }
    
    async def validate_facts(self, content: str, cross_reference_data: List[str] = None) -> Dict[str, Any]:
        """Validate factual claims in content"""
        
        validation_result = {
            'factual_accuracy_score': 0.5,
            'validated_facts': [],
            'potential_inaccuracies': [],
            'cross_reference_matches': 0,
            'validation_confidence': 0.5
        }
        
        try:
            # Extract potential facts
            extracted_facts = self._extract_facts(content)
            
            # Cross-reference with provided data
            if cross_reference_data:
                matches = self._cross_reference_facts(extracted_facts, cross_reference_data)
                validation_result['cross_reference_matches'] = matches
                validation_result['factual_accuracy_score'] += min(matches * 0.1, 0.3)
            
            # Use LLM for fact validation
            llm_validation = await self._llm_fact_validation(content)
            validation_result.update(llm_validation)
            
            # Calculate final confidence
            validation_result['validation_confidence'] = min(
                validation_result['factual_accuracy_score'] * 1.2, 1.0
            )
            
        except Exception as e:
            logger.error(f"Fact validation failed: {e}")
        
        return validation_result
    
    def _extract_facts(self, content: str) -> Dict[str, List[str]]:
        """Extract potential facts from content"""
        
        import re
        facts = {}
        
        for pattern_name, pattern in self.fact_patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                facts[pattern_name] = matches
        
        return facts
    
    def _cross_reference_facts(self, facts: Dict[str, List[str]], reference_data: List[str]) -> int:
        """Cross-reference extracted facts with reference data"""
        
        matches = 0
        
        for fact_type, fact_list in facts.items():
            for fact in fact_list:
                for ref_content in reference_data:
                    if fact.lower() in ref_content.lower():
                        matches += 1
                        break
        
        return matches
    
    async def _llm_fact_validation(self, content: str) -> Dict[str, Any]:
        """Use LLM to validate facts and identify potential issues"""
        
        prompt = f"""
        Analyze this content for factual accuracy and identify any potential inaccuracies or claims that need verification:
        
        Content: {content}
        
        Please identify:
        1. Factual claims that appear accurate
        2. Claims that seem questionable or need verification
        3. Overall assessment of factual reliability (scale 1-10)
        
        Format your response clearly with sections for each category.
        """
        
        try:
            response = await self.llm_manager.generate_response(
                prompt, QueryType.ANALYSIS,
                system_message="You are an expert fact-checker. Be thorough but fair in your analysis."
            )
            
            # Parse LLM response
            return self._parse_fact_validation_response(response.content)
            
        except Exception as e:
            logger.error(f"LLM fact validation failed: {e}")
            return {
                'validated_facts': [],
                'potential_inaccuracies': [],
                'factual_accuracy_score': 0.5
            }
    
    def _parse_fact_validation_response(self, response: str) -> Dict[str, Any]:
        """Parse fact validation response from LLM"""
        
        result = {
            'validated_facts': [],
            'potential_inaccuracies': [],
            'factual_accuracy_score': 0.5
        }
        
        # Simple parsing - can be enhanced
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if 'accurate' in line.lower() and ('claim' in line.lower() or 'fact' in line.lower()):
                current_section = 'validated'
            elif 'questionable' in line.lower() or 'verification' in line.lower():
                current_section = 'questionable'
            elif line and current_section:
                if current_section == 'validated':
                    result['validated_facts'].append(line)
                elif current_section == 'questionable':
                    result['potential_inaccuracies'].append(line)
            
            # Look for numerical score
            import re
            score_match = re.search(r'\b([1-9]|10)\b', line)
            if score_match and ('reliability' in line.lower() or 'accuracy' in line.lower()):
                result['factual_accuracy_score'] = float(score_match.group(1)) / 10
        
        return result


class TrustLayer:
    """
    Advanced trust layer providing comprehensive confidence scoring and transparency.
    
    Features:
    1. Multi-dimensional confidence assessment
    2. Source credibility tracking and scoring
    3. Automated fact checking and validation
    4. Cross-validation across multiple sources
    5. Temporal reliability assessment
    6. Comprehensive trust indicators and risk factors
    """
    
    def __init__(self):
        self.source_tracker = SourceCredibilityTracker()
        self.llm_manager = LLMManager()
        self.fact_checker = FactChecker(self.llm_manager)
        
        # Trust assessment history
        self.assessment_history: List[TrustAssessment] = []
        
        logger.info("Trust Layer initialized")
    
    async def assess_trust(
        self,
        content: str,
        sources: List[Dict[str, Any]],
        query_context: Optional[str] = None,
        cross_reference_data: Optional[List[str]] = None
    ) -> TrustAssessment:
        """
        Perform comprehensive trust assessment.
        
        Args:
            content: Content to assess
            sources: List of source information
            query_context: Original query context
            cross_reference_data: Additional data for cross-validation
            
        Returns:
            Comprehensive TrustAssessment
        """
        
        try:
            # Initialize confidence metrics
            confidence_metrics = {}
            
            # Assess factual accuracy
            fact_validation = await self.fact_checker.validate_facts(content, cross_reference_data)
            confidence_metrics[ConfidenceCategory.FACTUAL_ACCURACY] = ConfidenceMetric(
                category=ConfidenceCategory.FACTUAL_ACCURACY,
                score=fact_validation['factual_accuracy_score'],
                method=ValidationMethod.AUTOMATED_FACT_CHECK,
                explanation=f"Validated {len(fact_validation['validated_facts'])} facts, "
                          f"{len(fact_validation['potential_inaccuracies'])} potential issues",
                evidence_count=len(fact_validation['validated_facts'])
            )
            
            # Assess source reliability
            source_reliability = await self._assess_source_reliability(sources)
            confidence_metrics[ConfidenceCategory.SOURCE_RELIABILITY] = ConfidenceMetric(
                category=ConfidenceCategory.SOURCE_RELIABILITY,
                score=source_reliability['average_credibility'],
                method=ValidationMethod.SOURCE_AUTHORITY,
                explanation=f"Average source credibility: {source_reliability['average_credibility']:.2f}",
                evidence_count=len(sources)
            )
            
            # Assess data freshness
            data_freshness = self._assess_data_freshness(sources)
            confidence_metrics[ConfidenceCategory.DATA_FRESHNESS] = ConfidenceMetric(
                category=ConfidenceCategory.DATA_FRESHNESS,
                score=data_freshness['freshness_score'],
                method=ValidationMethod.TEMPORAL_CONSISTENCY,
                explanation=f"Average data age: {data_freshness['average_age_hours']:.1f} hours",
                evidence_count=data_freshness['timestamped_sources']
            )
            
            # Assess cross-validation
            cross_validation = self._assess_cross_validation(sources, content)
            confidence_metrics[ConfidenceCategory.CROSS_VALIDATION] = ConfidenceMetric(
                category=ConfidenceCategory.CROSS_VALIDATION,
                score=cross_validation['validation_score'],
                method=ValidationMethod.CROSS_REFERENCE,
                explanation=f"Cross-validated across {cross_validation['unique_sources']} sources",
                evidence_count=cross_validation['validation_points']
            )
            
            # Assess completeness
            completeness = await self._assess_completeness(content, query_context)
            confidence_metrics[ConfidenceCategory.COMPLETENESS] = ConfidenceMetric(
                category=ConfidenceCategory.COMPLETENESS,
                score=completeness['completeness_score'],
                method=ValidationMethod.EXPERT_VERIFICATION,
                explanation=completeness['explanation'],
                evidence_count=completeness['coverage_points']
            )
            
            # Assess consistency
            consistency = await self._assess_consistency(content, sources)
            confidence_metrics[ConfidenceCategory.CONSISTENCY] = ConfidenceMetric(
                category=ConfidenceCategory.CONSISTENCY,
                score=consistency['consistency_score'],
                method=ValidationMethod.PEER_CONSENSUS,
                explanation=consistency['explanation'],
                evidence_count=consistency['consistency_checks']
            )
            
            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(confidence_metrics)
            
            # Determine trust level
            trust_level = self._determine_trust_level(overall_confidence)
            
            # Generate trust indicators and risk factors
            trust_indicators = self._generate_trust_indicators(confidence_metrics, sources)
            risk_factors = self._generate_risk_factors(confidence_metrics, sources)
            
            # Create source credibility scores
            source_credibility_scores = {}
            for source in sources:
                source_id = source.get('id', source.get('name', 'unknown'))
                source_name = source.get('name', source_id)
                profile = self.source_tracker.get_or_create_profile(source_id, source_name)
                source_credibility_scores[source_name] = self.source_tracker.calculate_source_credibility(source_id)
            
            # Create trust assessment
            assessment = TrustAssessment(
                overall_confidence=overall_confidence,
                trust_level=trust_level,
                confidence_metrics=confidence_metrics,
                validation_methods=list(set(metric.method for metric in confidence_metrics.values())),
                trust_indicators=trust_indicators,
                risk_factors=risk_factors,
                source_credibility_scores=source_credibility_scores,
                temporal_reliability=data_freshness['freshness_score'],
                cross_validation_score=cross_validation['validation_score'],
                assessment_metadata={
                    'total_sources': len(sources),
                    'assessment_timestamp': datetime.now(timezone.utc).isoformat(),
                    'query_context': query_context,
                    'validation_methods_used': len(set(metric.method for metric in confidence_metrics.values()))
                }
            )
            
            # Store assessment history
            self.assessment_history.append(assessment)
            
            return assessment
            
        except Exception as e:
            logger.error(f"Trust assessment failed: {e}")
            raise
    
    async def _assess_source_reliability(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess reliability of information sources"""
        
        credibility_scores = []
        
        for source in sources:
            source_id = source.get('id', source.get('name', 'unknown'))
            source_name = source.get('name', source_id)
            
            # Get or create profile
            profile = self.source_tracker.get_or_create_profile(source_id, source_name)
            credibility = self.source_tracker.calculate_source_credibility(source_id)
            credibility_scores.append(credibility)
        
        return {
            'average_credibility': statistics.mean(credibility_scores) if credibility_scores else 0.0,
            'credibility_scores': credibility_scores,
            'high_credibility_sources': len([s for s in credibility_scores if s > 0.7]),
            'low_credibility_sources': len([s for s in credibility_scores if s < 0.3])
        }
    
    def _assess_data_freshness(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess freshness of data from sources"""
        
        now = datetime.now(timezone.utc)
        ages = []
        timestamped_count = 0
        
        for source in sources:
            timestamp_str = source.get('timestamp')
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    age_hours = (now - timestamp).total_seconds() / 3600
                    ages.append(age_hours)
                    timestamped_count += 1
                except:
                    pass
        
        if ages:
            average_age = statistics.mean(ages)
            # Freshness score: higher for more recent data
            freshness_score = max(0.0, 1.0 - (average_age / (24 * 7)))  # Degrade over a week
        else:
            average_age = 0
            freshness_score = 0.5  # Neutral if no timestamps
        
        return {
            'freshness_score': freshness_score,
            'average_age_hours': average_age,
            'timestamped_sources': timestamped_count,
            'total_sources': len(sources)
        }
    
    def _assess_cross_validation(self, sources: List[Dict[str, Any]], content: str) -> Dict[str, Any]:
        """Assess cross-validation across sources"""
        
        unique_sources = len(set(source.get('name', 'unknown') for source in sources))
        unique_types = len(set(source.get('type', 'unknown') for source in sources))
        
        # Simple validation based on source diversity
        validation_score = min(unique_sources / 3, 1.0) * 0.7 + min(unique_types / 2, 1.0) * 0.3
        
        return {
            'validation_score': validation_score,
            'unique_sources': unique_sources,
            'unique_types': unique_types,
            'validation_points': unique_sources + unique_types
        }
    
    async def _assess_completeness(self, content: str, query_context: Optional[str]) -> Dict[str, Any]:
        """Assess completeness of information relative to query"""
        
        if not query_context:
            return {
                'completeness_score': 0.7,
                'explanation': 'No query context provided for completeness assessment',
                'coverage_points': 1
            }
        
        prompt = f"""
        Assess how completely this content answers the original query:
        
        Query: {query_context}
        Content: {content}
        
        Rate completeness on a scale of 1-10 and explain what aspects are well-covered and what might be missing.
        """
        
        try:
            response = await self.llm_manager.generate_response(
                prompt, QueryType.ANALYSIS,
                system_message="Assess information completeness objectively."
            )
            
            # Parse completeness score
            import re
            score_match = re.search(r'\b([1-9]|10)\b', response.content)
            completeness_score = float(score_match.group(1)) / 10 if score_match else 0.7
            
            return {
                'completeness_score': completeness_score,
                'explanation': response.content[:200] + "..." if len(response.content) > 200 else response.content,
                'coverage_points': len(response.content.split())  # Rough measure
            }
            
        except Exception as e:
            logger.error(f"Completeness assessment failed: {e}")
            return {
                'completeness_score': 0.5,
                'explanation': 'Completeness assessment unavailable',
                'coverage_points': 0
            }
    
    async def _assess_consistency(self, content: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess consistency of information across sources"""
        
        if len(sources) < 2:
            return {
                'consistency_score': 1.0,
                'explanation': 'Single source - no consistency issues detected',
                'consistency_checks': 1
            }
        
        prompt = f"""
        Analyze this synthesized content for internal consistency and logical coherence:
        
        Content: {content}
        Number of sources: {len(sources)}
        
        Rate consistency on a scale of 1-10 and identify any contradictions or inconsistencies.
        """
        
        try:
            response = await self.llm_manager.generate_response(
                prompt, QueryType.ANALYSIS,
                system_message="Assess information consistency and identify contradictions."
            )
            
            # Parse consistency score
            import re
            score_match = re.search(r'\b([1-9]|10)\b', response.content)
            consistency_score = float(score_match.group(1)) / 10 if score_match else 0.7
            
            return {
                'consistency_score': consistency_score,
                'explanation': response.content[:200] + "..." if len(response.content) > 200 else response.content,
                'consistency_checks': len(sources)
            }
            
        except Exception as e:
            logger.error(f"Consistency assessment failed: {e}")
            return {
                'consistency_score': 0.5,
                'explanation': 'Consistency assessment unavailable',
                'consistency_checks': 0
            }
    
    def _calculate_overall_confidence(self, confidence_metrics: Dict[ConfidenceCategory, ConfidenceMetric]) -> float:
        """Calculate overall confidence from individual metrics"""
        
        # Weighted average of confidence metrics
        weights = {
            ConfidenceCategory.FACTUAL_ACCURACY: 0.25,
            ConfidenceCategory.SOURCE_RELIABILITY: 0.20,
            ConfidenceCategory.DATA_FRESHNESS: 0.15,
            ConfidenceCategory.CROSS_VALIDATION: 0.15,
            ConfidenceCategory.COMPLETENESS: 0.15,
            ConfidenceCategory.CONSISTENCY: 0.10
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for category, metric in confidence_metrics.items():
            weight = weights.get(category, 0.1)
            weighted_sum += metric.score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.5
    
    def _determine_trust_level(self, confidence_score: float) -> TrustLevel:
        """Determine trust level based on confidence score"""
        
        if confidence_score >= 0.9:
            return TrustLevel.VERY_HIGH
        elif confidence_score >= 0.75:
            return TrustLevel.HIGH
        elif confidence_score >= 0.6:
            return TrustLevel.MEDIUM
        elif confidence_score >= 0.4:
            return TrustLevel.LOW
        else:
            return TrustLevel.VERY_LOW
    
    def _generate_trust_indicators(
        self, 
        confidence_metrics: Dict[ConfidenceCategory, ConfidenceMetric],
        sources: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate positive trust indicators"""
        
        indicators = []
        
        # Check for high-confidence metrics
        for category, metric in confidence_metrics.items():
            if metric.score >= 0.8:
                if category == ConfidenceCategory.FACTUAL_ACCURACY:
                    indicators.append("High factual accuracy confirmed")
                elif category == ConfidenceCategory.SOURCE_RELIABILITY:
                    indicators.append("Reliable source credentials verified")
                elif category == ConfidenceCategory.DATA_FRESHNESS:
                    indicators.append("Recent data (<24 hours)")
                elif category == ConfidenceCategory.CROSS_VALIDATION:
                    indicators.append("Multiple source confirmation")
                elif category == ConfidenceCategory.COMPLETENESS:
                    indicators.append("Comprehensive information coverage")
                elif category == ConfidenceCategory.CONSISTENCY:
                    indicators.append("Consistent information across sources")
        
        # Additional source-based indicators
        if len(sources) >= 3:
            indicators.append("Multiple independent sources")
        
        return indicators
    
    def _generate_risk_factors(
        self, 
        confidence_metrics: Dict[ConfidenceCategory, ConfidenceMetric],
        sources: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate risk factors and concerns"""
        
        risk_factors = []
        
        # Check for low-confidence metrics
        for category, metric in confidence_metrics.items():
            if metric.score <= 0.4:
                if category == ConfidenceCategory.FACTUAL_ACCURACY:
                    risk_factors.append("Potential factual inaccuracies detected")
                elif category == ConfidenceCategory.SOURCE_RELIABILITY:
                    risk_factors.append("Low source credibility scores")
                elif category == ConfidenceCategory.DATA_FRESHNESS:
                    risk_factors.append("Outdated information (>7 days)")
                elif category == ConfidenceCategory.CROSS_VALIDATION:
                    risk_factors.append("Limited cross-validation")
                elif category == ConfidenceCategory.COMPLETENESS:
                    risk_factors.append("Incomplete information coverage")
                elif category == ConfidenceCategory.CONSISTENCY:
                    risk_factors.append("Inconsistencies or contradictions found")
        
        # Additional risk factors
        if len(sources) == 1:
            risk_factors.append("Single source dependency")
        
        return risk_factors
    
    def get_trust_statistics(self) -> Dict[str, Any]:
        """Get trust layer statistics and insights"""
        
        if not self.assessment_history:
            return {'message': 'No assessments performed yet'}
        
        recent_assessments = self.assessment_history[-100:]  # Last 100 assessments
        
        confidence_scores = [a.overall_confidence for a in recent_assessments]
        trust_levels = [a.trust_level.value for a in recent_assessments]
        
        return {
            'total_assessments': len(self.assessment_history),
            'recent_assessments': len(recent_assessments),
            'average_confidence': statistics.mean(confidence_scores),
            'confidence_trend': confidence_scores[-10:] if len(confidence_scores) >= 10 else confidence_scores,
            'trust_level_distribution': {
                level: trust_levels.count(level) for level in set(trust_levels)
            },
            'source_profiles': len(self.source_tracker.source_profiles),
            'domain_experts': len(self.source_tracker.domain_experts)
        }