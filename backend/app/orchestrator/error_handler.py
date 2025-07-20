"""
Error Handler for Orchestrator
Comprehensive error handling and recovery for the SingleBrief orchestrator
"""

import logging
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Categories of errors"""

    MODULE_FAILURE = "module_failure"
    PARSING_ERROR = "parsing_error"
    LLM_ERROR = "llm_error"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    DATA_ERROR = "data_error"
    TIMEOUT_ERROR = "timeout_error"
    CONFIGURATION_ERROR = "configuration_error"
    UNKNOWN_ERROR = "unknown_error"

@dataclass

class ErrorContext:
    """Context information for errors"""

    error_id: str
    timestamp: datetime
    query_id: Optional[str] = None
    user_id: Optional[str] = None
    module_name: Optional[str] = None
    error_category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    error_message: str = ""
    stack_trace: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

class ErrorHandler:
    """
    Comprehensive error handling system for the orchestrator.

    Features:
    1. Error classification and severity assessment
    2. Automatic recovery strategies
    3. Fallback response generation
    4. Error logging and monitoring
    5. Circuit breaker patterns for failing modules
    """

    def __init__(self):
        self.error_history: List[ErrorContext] = []
        self.module_failure_counts: Dict[str, int] = {}
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}

        # Recovery strategies by error type
        self.recovery_strategies = {
            ErrorCategory.MODULE_FAILURE: self._handle_module_failure,
            ErrorCategory.LLM_ERROR: self._handle_llm_error,
            ErrorCategory.NETWORK_ERROR: self._handle_network_error,
            ErrorCategory.TIMEOUT_ERROR: self._handle_timeout_error,
            ErrorCategory.RATE_LIMIT_ERROR: self._handle_rate_limit_error,
            ErrorCategory.DATA_ERROR: self._handle_data_error,
            ErrorCategory.PARSING_ERROR: self._handle_parsing_error,
            ErrorCategory.AUTHENTICATION_ERROR: self._handle_authentication_error,
            ErrorCategory.CONFIGURATION_ERROR: self._handle_configuration_error,
        }

        logger.info("ErrorHandler initialized")

    async def handle_query_error(
        self,
        query: str,
        context: Any,
        error: Exception,
        module_name: Optional[str] = None,
    ) -> str:
        """
        Handle query processing errors and attempt recovery.

        Args:
            query: Original query that failed
            context: Query context
            error: The exception that occurred
            module_name: Name of module where error occurred

        Returns:
            Fallback response string
        """
        try:
            # Create error context
            error_context = self._create_error_context(
                error, query, context, module_name
            )

            # Log error
            self._log_error(error_context)

            # Update failure tracking
            self._update_failure_tracking(error_context)

            # Attempt recovery
            recovery_response = await self._attempt_recovery(
                error_context, query, context
            )

            if recovery_response:
                error_context.recovery_attempted = True
                error_context.recovery_successful = True
                return recovery_response

            # Generate fallback response
            fallback_response = self._generate_fallback_response(error_context, query)

            return fallback_response

        except Exception as recovery_error:
            logger.error(f"Error recovery failed: {recovery_error}")
            return self._generate_emergency_response(query)

    def _create_error_context(
        self,
        error: Exception,
        query: str,
        context: Any,
        module_name: Optional[str] = None,
    ) -> ErrorContext:
        """Create comprehensive error context"""

        error_category = self._classify_error(error)
        severity = self._assess_severity(error, error_category, module_name)

        error_context = ErrorContext(
            error_id=f"err_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(error)}",
            timestamp=datetime.now(timezone.utc),
            query_id=getattr(context, "query_id", None),
            user_id=getattr(context, "user_id", None),
            module_name=module_name,
            error_category=error_category,
            severity=severity,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            metadata={
                "query_length": len(query),
                "error_type": type(error).__name__,
                "context_available": context is not None,
            },
        )

        self.error_history.append(error_context)
        return error_context

    def _classify_error(self, error: Exception) -> ErrorCategory:
        """Classify error into appropriate category"""
        error_type = type(error).__name__
        error_message = str(error).lower()

        # Classification rules
        if "timeout" in error_message or error_type in [
            "TimeoutError",
            "asyncio.TimeoutError",
        ]:
            return ErrorCategory.TIMEOUT_ERROR

        if "network" in error_message or "connection" in error_message:
            return ErrorCategory.NETWORK_ERROR

        if "rate limit" in error_message or "quota" in error_message:
            return ErrorCategory.RATE_LIMIT_ERROR

        if "authentication" in error_message or "unauthorized" in error_message:
            return ErrorCategory.AUTHENTICATION_ERROR

        if "parse" in error_message or "json" in error_message:
            return ErrorCategory.PARSING_ERROR

        if "openai" in error_message or "llm" in error_message:
            return ErrorCategory.LLM_ERROR

        if "config" in error_message or "setting" in error_message:
            return ErrorCategory.CONFIGURATION_ERROR

        if "data" in error_message or "value" in error_message:
            return ErrorCategory.DATA_ERROR

        return ErrorCategory.UNKNOWN_ERROR

    def _assess_severity(
        self, error: Exception, category: ErrorCategory, module_name: Optional[str]
    ) -> ErrorSeverity:
        """Assess error severity"""

        # Critical errors
        if category in [
            ErrorCategory.AUTHENTICATION_ERROR,
            ErrorCategory.CONFIGURATION_ERROR,
        ]:
            return ErrorSeverity.CRITICAL

        # High severity errors
        if category in [ErrorCategory.LLM_ERROR, ErrorCategory.RATE_LIMIT_ERROR]:
            return ErrorSeverity.HIGH

        # Check module failure frequency
        if module_name:
            failure_count = self.module_failure_counts.get(module_name, 0)
            if failure_count > 5:
                return ErrorSeverity.HIGH
            elif failure_count > 2:
                return ErrorSeverity.MEDIUM

        # Medium severity by default
        if category in [ErrorCategory.MODULE_FAILURE, ErrorCategory.NETWORK_ERROR]:
            return ErrorSeverity.MEDIUM

        return ErrorSeverity.LOW

    def _log_error(self, error_context: ErrorContext):
        """Log error with appropriate level"""
        log_message = f"Error {error_context.error_id}: {error_context.error_message}"

        if error_context.module_name:
            log_message += f" (Module: {error_context.module_name})"

        if error_context.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, extra={"error_context": error_context})
        elif error_context.severity == ErrorSeverity.HIGH:
            logger.error(log_message, extra={"error_context": error_context})
        elif error_context.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message, extra={"error_context": error_context})
        else:
            logger.info(log_message, extra={"error_context": error_context})

    def _update_failure_tracking(self, error_context: ErrorContext):
        """Update failure tracking for modules and circuit breakers"""
        if error_context.module_name:
            module_name = error_context.module_name
            self.module_failure_counts[module_name] = (
                self.module_failure_counts.get(module_name, 0) + 1
            )

            # Implement circuit breaker logic
            failure_count = self.module_failure_counts[module_name]

            if failure_count >= 5:  # Circuit breaker threshold
                self.circuit_breakers[module_name] = {
                    "status": "open",
                    "opened_at": datetime.now(timezone.utc),
                    "failure_count": failure_count,
                }
                logger.warning(f"Circuit breaker opened for module {module_name}")

    async def _attempt_recovery(
        self, error_context: ErrorContext, query: str, context: Any
    ) -> Optional[str]:
        """Attempt to recover from the error"""

        recovery_strategy = self.recovery_strategies.get(error_context.error_category)
        if not recovery_strategy:
            return None

        try:
            return await recovery_strategy(error_context, query, context)
        except Exception as recovery_error:
            logger.error(f"Recovery strategy failed: {recovery_error}")
            return None

    # Recovery strategy implementations
    async def _handle_module_failure(
        self, error_context: ErrorContext, query: str, context: Any
    ) -> Optional[str]:
        """Handle module failure with alternative modules"""
        if not error_context.module_name:
            return None

        # Try to find alternative modules for the same capability
        # This would require integration with module registry
        logger.info(
            f"Attempting to route around failed module: {error_context.module_name}"
        )

        return f"I encountered an issue with one of my data sources, but I can still help you. Let me try a different approach to gather the information you need."

    async def _handle_llm_error(
        self, error_context: ErrorContext, query: str, context: Any
    ) -> Optional[str]:
        """Handle LLM/AI processing errors"""
        return "I'm experiencing some processing difficulties right now. Let me provide you with the raw data I've gathered, and you can let me know if you need specific analysis."

    async def _handle_network_error(
        self, error_context: ErrorContext, query: str, context: Any
    ) -> Optional[str]:
        """Handle network connectivity issues"""
        return "I'm having trouble connecting to some of your data sources. I'll provide what information I can access locally and retry the connection shortly."

    async def _handle_timeout_error(
        self, error_context: ErrorContext, query: str, context: Any
    ) -> Optional[str]:
        """Handle timeout errors"""
        return "Your query is taking longer than usual to process. I'll continue working on it in the background and can provide a partial response now if helpful."

    async def _handle_rate_limit_error(
        self, error_context: ErrorContext, query: str, context: Any
    ) -> Optional[str]:
        """Handle rate limiting from external services"""
        return "I've reached a temporary limit with one of the external services. I'll retry your request shortly, or you can try again in a few minutes."

    async def _handle_data_error(
        self, error_context: ErrorContext, query: str, context: Any
    ) -> Optional[str]:
        """Handle data parsing or validation errors"""
        return "I encountered some unexpected data format issues, but I can still provide you with available information. The data quality might be limited for this response."

    async def _handle_parsing_error(
        self, error_context: ErrorContext, query: str, context: Any
    ) -> Optional[str]:
        """Handle query parsing errors"""
        return "I had trouble understanding part of your query. Could you rephrase it, or would you like me to provide general information about what I found?"

    async def _handle_authentication_error(
        self, error_context: ErrorContext, query: str, context: Any
    ) -> Optional[str]:
        """Handle authentication issues"""
        return "I need to re-authenticate with one of your connected services. Please check your integrations in the settings, and I'll try to gather information from other available sources."

    async def _handle_configuration_error(
        self, error_context: ErrorContext, query: str, context: Any
    ) -> Optional[str]:
        """Handle configuration issues"""
        return "There appears to be a configuration issue that's preventing me from accessing some data sources. Please contact your administrator or check the system settings."

    def _generate_fallback_response(
        self, error_context: ErrorContext, query: str
    ) -> str:
        """Generate fallback response when recovery fails"""

        if error_context.severity == ErrorSeverity.CRITICAL:
            return f"I apologize, but I'm experiencing a critical system issue that prevents me from processing your query right now. Please try again later or contact support if the problem persists. (Error ID: {error_context.error_id})"

        if error_context.severity == ErrorSeverity.HIGH:
            return f"I encountered a significant issue while processing your query, but the system is still operational. Please try rephrasing your query or try again in a few minutes. (Error ID: {error_context.error_id})"

        return f"I had some trouble gathering complete information for your query, but I'm still operational. You might want to try a more specific query or check back shortly. (Error ID: {error_context.error_id})"

    def _generate_emergency_response(self, query: str) -> str:
        """Generate emergency response when all else fails"""
        return "I'm experiencing technical difficulties and cannot process your query at this time. Please try again later. If this problem persists, please contact support."

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        if not self.error_history:
            return {
                "total_errors": 0,
                "error_categories": {},
                "module_failures": {},
                "circuit_breakers": {},
            }

        # Calculate error statistics
        category_counts = {}
        severity_counts = {}

        for error in self.error_history[-100:]:  # Last 100 errors
            category = error.error_category.value
            severity = error.severity.value

            category_counts[category] = category_counts.get(category, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            "total_errors": len(self.error_history),
            "recent_errors": len(self.error_history[-24:]),  # Last 24 errors
            "error_categories": category_counts,
            "error_severities": severity_counts,
            "module_failures": dict(self.module_failure_counts),
            "circuit_breakers": dict(self.circuit_breakers),
            "last_error_time": (
                self.error_history[-1].timestamp.isoformat()
                if self.error_history
                else None
            ),
        }

    def reset_module_failures(self, module_name: str):
        """Reset failure count for a module"""
        if module_name in self.module_failure_counts:
            del self.module_failure_counts[module_name]

        if module_name in self.circuit_breakers:
            del self.circuit_breakers[module_name]

        logger.info(f"Reset failure tracking for module: {module_name}")

    def is_circuit_breaker_open(self, module_name: str) -> bool:
        """Check if circuit breaker is open for a module"""
        breaker = self.circuit_breakers.get(module_name)
        if not breaker:
            return False

        # Check if circuit breaker should be reset (after 5 minutes)
        opened_at = breaker["opened_at"]
        minutes_since = (datetime.now(timezone.utc) - opened_at).total_seconds() / 60

        if minutes_since > 5:  # Reset after 5 minutes
            del self.circuit_breakers[module_name]
            self.module_failure_counts[module_name] = 0
            logger.info(f"Circuit breaker reset for module: {module_name}")
            return False

        return breaker["status"] == "open"
