"""API endpoints for context-aware response generation."""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_async_session
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.ai.context_response import context_response_service

router = APIRouter()


class ContextualQueryRequest(BaseModel):
    """Request model for contextual query processing."""
    query: str = Field(..., min_length=1, description="User query")
    conversation_id: Optional[str] = Field(None, description="Optional conversation context")
    response_format: Optional[str] = Field(None, description="Preferred response format: conversational, structured, bullet_points")
    include_team_context: bool = Field(True, description="Whether to include team memory context")
    include_proactive_insights: bool = Field(True, description="Whether to include proactive insights")
    include_follow_ups: bool = Field(True, description="Whether to include follow-up suggestions")


class ResponseFormattingRequest(BaseModel):
    """Request model for response formatting."""
    content: str = Field(..., description="Response content to format")
    format_type: str = Field(..., description="Format type: conversational, structured, bullet_points")
    tone: Optional[str] = Field(None, description="Response tone: professional, casual, direct")
    detail_level: Optional[str] = Field(None, description="Detail level: brief, medium, detailed")


class ContextualResponseResponse(BaseModel):
    """Response model for contextual query processing."""
    user_id: str
    query: str
    context: Dict[str, Any]
    response_structure: Dict[str, Any]
    follow_up_suggestions: List[Dict[str, Any]]
    proactive_insights: List[Dict[str, Any]]
    personalization_applied: Dict[str, Any]
    generated_at: str


class FormattedResponseResponse(BaseModel):
    """Response model for formatted response."""
    content: str
    format: str
    tone: str
    detail_level: str
    technical_depth: str
    personalization_applied: Dict[str, Any]
    formatting_metadata: Dict[str, Any]


@router.post("/generate-context", response_model=ContextualResponseResponse)
async def generate_contextual_response(
    request: ContextualQueryRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> ContextualResponseResponse:
    """
    Generate context-aware response structure for a user query.
    
    Analyzes user query, builds comprehensive context from memory,
    preferences, and team data, and provides personalized response
    structure with follow-up suggestions and proactive insights.
    """
    try:
        context_response_service.session = session
        response = await context_response_service.generate_contextualized_response(
            user_id=current_user.id,
            query=request.query,
            conversation_id=request.conversation_id,
            response_format=request.response_format,
            include_team_context=request.include_team_context
        )
        
        # Filter response based on request preferences
        if not request.include_follow_ups:
            response["follow_up_suggestions"] = []
        if not request.include_proactive_insights:
            response["proactive_insights"] = []
        
        return ContextualResponseResponse(**response)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate contextual response: {str(e)}"
        )


@router.post("/format-response", response_model=FormattedResponseResponse)
async def format_response_content(
    request: ResponseFormattingRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> FormattedResponseResponse:
    """
    Format response content based on user preferences.
    
    Takes response content and applies user-specific formatting,
    tone, and structure preferences to create personalized output.
    """
    try:
        context_response_service.session = session
        
        # Build minimal response structure from request
        response_structure = {
            "format": request.format_type,
            "tone": request.tone or "professional",
            "detail_level": request.detail_level or "medium",
            "technical_depth": "medium",
            "personalization_elements": {}
        }
        
        # Apply formatting
        formatted = await context_response_service.apply_response_formatting(
            response_content=request.content,
            response_structure=response_structure,
            context={}  # Minimal context for formatting-only operation
        )
        
        return FormattedResponseResponse(**formatted)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to format response: {str(e)}"
        )


@router.get("/context/{user_id}", response_model=Dict[str, Any])
async def get_user_context_summary(
    user_id: str,
    topic: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get user context summary for personalization.
    
    Returns a summary of user context including preferences,
    recent memories, patterns, and team information that can
    be used for response personalization.
    """
    # Verify user has permission to access context
    if current_user.id != user_id and not current_user.is_admin:
        if (current_user.organization_id != await _get_user_organization(session, user_id) or 
            current_user.role not in ["team_lead", "admin"]):
            raise HTTPException(
                status_code=403, 
                detail="Not authorized to access this user's context"
            )
    
    try:
        context_response_service.session = session
        
        # Build context for a generic query (or topic-specific if provided)
        query = f"Information about {topic}" if topic else "General information"
        
        context = await context_response_service._build_comprehensive_context(
            session, user_id, query, None, True
        )
        
        # Get user preferences
        user_preferences = await context_response_service._get_user_response_preferences(
            session, user_id
        )
        
        return {
            "user_id": user_id,
            "context_summary": {
                "memory_count": context.get("user_memory_context", {}).get("total_memories", 0),
                "team_context_available": len(context.get("team_context", {})) > 0,
                "recent_decisions": len(context.get("recent_decisions", {}).get("decisions", [])),
                "behavior_patterns": len(context.get("historical_patterns", {}).get("patterns", [])),
                "topic_preferences": len(context.get("topic_preferences", {}))
            },
            "communication_preferences": user_preferences.get("communication_style", {}),
            "format_preferences": user_preferences.get("format_preferences", {}),
            "confidence_levels": user_preferences.get("confidence_levels", {}),
            "generated_at": context.get("generated_at", "")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user context: {str(e)}"
        )


@router.get("/preferences/response-style", response_model=Dict[str, Any])
async def get_response_style_preferences(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get user's response style preferences.
    
    Returns learned and manually set preferences for response
    formatting, tone, detail level, and communication style.
    """
    try:
        context_response_service.session = session
        
        preferences = await context_response_service._get_user_response_preferences(
            session, current_user.id
        )
        
        return {
            "user_id": current_user.id,
            "preferences": preferences,
            "preference_summary": {
                "communication_style_set": len(preferences.get("communication_style", {})) > 0,
                "format_preferences_set": len(preferences.get("format_preferences", {})) > 0,
                "confidence_range": {
                    "min": min(preferences.get("confidence_levels", {}).values()) if preferences.get("confidence_levels") else 0,
                    "max": max(preferences.get("confidence_levels", {}).values()) if preferences.get("confidence_levels") else 0,
                    "avg": sum(preferences.get("confidence_levels", {}).values()) / max(len(preferences.get("confidence_levels", {})), 1)
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get response style preferences: {str(e)}"
        )


@router.post("/query/interpret", response_model=Dict[str, Any])
async def interpret_query_with_context(
    query: str,
    conversation_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Interpret user query with historical context and memory.
    
    Analyzes query intent, extracts entities, and provides
    context-enhanced interpretation using user memory and patterns.
    """
    try:
        context_response_service.session = session
        
        # Analyze query context
        query_context = await context_response_service._analyze_query_context(query)
        
        # Get relevant context for interpretation
        context = await context_response_service._build_comprehensive_context(
            session, current_user.id, query, conversation_id, True
        )
        
        # Enhanced interpretation using context
        interpretation = {
            "original_query": query,
            "query_analysis": query_context,
            "context_enhanced": {
                "has_historical_context": len(context.get("user_memory_context", {}).get("memories_by_type", {})) > 0,
                "has_team_context": len(context.get("team_context", {})) > 0,
                "has_conversation_context": len(context.get("conversation_context", {})) > 0,
                "relevant_patterns": context.get("historical_patterns", {}).get("patterns_found", 0),
                "recent_decisions_relevant": len(context.get("recent_decisions", {}).get("decisions", []))
            },
            "interpretation_confidence": self._calculate_interpretation_confidence(query_context, context),
            "suggested_clarifications": self._generate_clarification_suggestions(query_context, context),
            "context_disambiguation": self._generate_disambiguation_options(query, context)
        }
        
        return interpretation
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to interpret query: {str(e)}"
        )


def _calculate_interpretation_confidence(query_context: Dict[str, Any], context: Dict[str, Any]) -> float:
    """Calculate confidence score for query interpretation."""
    confidence = 0.5  # Base confidence
    
    # Boost confidence if query is clear
    if query_context.get("is_question"):
        confidence += 0.2
    
    # Boost if we have relevant context
    if context.get("user_memory_context", {}).get("total_memories", 0) > 0:
        confidence += 0.1
    
    if context.get("conversation_context", {}).get("message_count", 0) > 0:
        confidence += 0.1
    
    # Boost for clear topics
    if len(query_context.get("detected_topics", [])) > 0:
        confidence += 0.1
    
    return min(confidence, 1.0)


def _generate_clarification_suggestions(query_context: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
    """Generate clarification suggestions based on context."""
    suggestions = []
    
    # If query is vague
    if query_context.get("complexity") == "low" and len(query_context.get("detected_topics", [])) == 0:
        suggestions.append("Could you provide more specific details about what you're looking for?")
    
    # If multiple topics detected
    if len(query_context.get("detected_topics", [])) > 2:
        suggestions.append("Which aspect would you like me to focus on?")
    
    # If urgency is unclear but seems important
    if query_context.get("urgency_level") == "normal" and "important" in query_context.get("query", "").lower():
        suggestions.append("Is this time-sensitive or urgent?")
    
    return suggestions


def _generate_disambiguation_options(query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate disambiguation options based on context."""
    options = []
    
    # Based on team context
    team_memories = context.get("team_context", {}).get("relevant_memories", [])
    if team_memories:
        options.append({
            "interpretation": "Team-related query",
            "description": "Based on your team's recent activities and shared knowledge",
            "confidence": 0.7
        })
    
    # Based on user patterns
    patterns = context.get("historical_patterns", {}).get("patterns", [])
    for pattern in patterns[:2]:  # Top 2 patterns
        options.append({
            "interpretation": f"Related to your {pattern.get('pattern_name', 'activity pattern')}",
            "description": f"Based on your {pattern.get('pattern_type', 'behavioral')} patterns",
            "confidence": pattern.get("predictive_value", 0.5)
        })
    
    return options


async def _get_user_organization(session: AsyncSession, user_id: str) -> str:
    """Helper function to get user's organization ID."""
    from sqlalchemy import select
    
    query = select(User.organization_id).where(User.id == user_id)
    result = await session.execute(query)
    org_id = result.scalar_one_or_none()
    
    if not org_id:
        raise HTTPException(status_code=404, detail="User not found")
    
    return org_id