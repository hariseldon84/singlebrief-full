"""
Module Registry for Orchestrator
Manages registration and coordination of all SingleBrief modules
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol

# Temporarily commented out for dependency issues
# from langchain.tools import Any

logger = logging.getLogger(__name__)

class SingleBriefModule(Protocol):
    """Protocol defining the interface all SingleBrief modules must implement"""

    @property
    def name(self) -> str:
        """Module name"""
        ...

    @property
    def capabilities(self) -> List[str]:
        """List of capabilities this module provides"""
        ...

    async def process_query(
        self, query: Dict[str, Any], context: Any
    ) -> Dict[str, Any]:
        """Process a query and return results"""
        ...

    async def get_health_status(self) -> Dict[str, Any]:
        """Get module health status"""
        ...

    def get_tools(self) -> List[Any]:
        """Get LangChain tools this module provides"""
        ...

@dataclass

class ModuleInfo:
    """Information about a registered module"""

    name: str
    module: SingleBriefModule
    capabilities: List[str]
    priority: int
    is_enabled: bool
    registered_at: datetime
    last_health_check: Optional[datetime] = None
    health_status: str = "unknown"

class ModuleRegistry:
    """
    Registry for managing SingleBrief modules.

    Handles module registration, discovery, health monitoring,
    and coordination between modules.
    """

    def __init__(self):
        self._modules: Dict[str, ModuleInfo] = {}
        self._capability_map: Dict[str, List[str]] = {}
        self._tools_cache: Optional[List[Any]] = None

        # Register built-in modules
        self._register_builtin_modules()

        logger.info("ModuleRegistry initialized")

    def _register_builtin_modules(self):
        """Register built-in modules"""
        # Register mock modules for now
        mock_modules = [
            MockTeamCommsModule(),
            MockMemoryEngineModule(),
            MockIntegrationHubModule(),
            MockTrustLayerModule(),
        ]

        for module in mock_modules:
            self.register_module(module, priority=1)

    def register_module(
        self, module: SingleBriefModule, priority: int = 1, enabled: bool = True
    ) -> bool:
        """
        Register a module with the registry.

        Args:
            module: The module to register
            priority: Module priority (higher = more important)
            enabled: Whether the module is enabled

        Returns:
            True if registration successful
        """
        try:
            module_info = ModuleInfo(
                name=module.name,
                module=module,
                capabilities=module.capabilities,
                priority=priority,
                is_enabled=enabled,
                registered_at=datetime.now(timezone.utc),
            )

            self._modules[module.name] = module_info

            # Update capability mapping
            for capability in module.capabilities:
                if capability not in self._capability_map:
                    self._capability_map[capability] = []
                self._capability_map[capability].append(module.name)

            # Clear tools cache
            self._tools_cache = None

            logger.info(
                f"Registered module: {module.name} with capabilities: {module.capabilities}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to register module {module.name}: {e}")
            return False

    def unregister_module(self, module_name: str) -> bool:
        """Unregister a module"""
        if module_name in self._modules:
            module_info = self._modules[module_name]

            # Remove from capability mapping
            for capability in module_info.capabilities:
                if capability in self._capability_map:
                    if module_name in self._capability_map[capability]:
                        self._capability_map[capability].remove(module_name)
                    if not self._capability_map[capability]:
                        del self._capability_map[capability]

            del self._modules[module_name]
            self._tools_cache = None

            logger.info(f"Unregistered module: {module_name}")
            return True

        return False

    def get_module(self, module_name: str) -> Optional[SingleBriefModule]:
        """Get a module by name"""
        module_info = self._modules.get(module_name)
        return module_info.module if module_info and module_info.is_enabled else None

    def get_modules_by_capability(self, capability: str) -> List[SingleBriefModule]:
        """Get all modules that provide a specific capability"""
        module_names = self._capability_map.get(capability, [])
        modules = []

        for name in module_names:
            module_info = self._modules.get(name)
            if module_info and module_info.is_enabled:
                modules.append(module_info.module)

        return modules

    def get_registered_modules(self) -> List[str]:
        """Get list of registered module names"""
        return list(self._modules.keys())

    def is_module_available(self, module_name: str) -> bool:
        """Check if a module is available and enabled"""
        module_info = self._modules.get(module_name)
        return module_info is not None and module_info.is_enabled

    def get_available_tools(self) -> List[Any]:
        """Get all tools from enabled modules"""
        if self._tools_cache is not None:
            return self._tools_cache

        tools = []
        for module_info in self._modules.values():
            if module_info.is_enabled:
                try:
                    module_tools = module_info.module.get_tools()
                    tools.extend(module_tools)
                except Exception as e:
                    logger.error(f"Failed to get tools from {module_info.name}: {e}")

        self._tools_cache = tools
        return tools

    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all modules"""
        results = {}

        for name, module_info in self._modules.items():
            try:
                health_status = await module_info.module.get_health_status()
                module_info.last_health_check = datetime.now(timezone.utc)
                module_info.health_status = health_status.get("status", "unknown")
                results[name] = health_status
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                results[name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

        return results

# Mock modules for initial implementation

class MockTeamCommsModule:
    """Mock Team Communications Crawler module"""

    @property
    def name(self) -> str:
        return "team_comms_crawler"

    @property
    def capabilities(self) -> List[str]:
        return ["team_communication", "slack_data", "email_data", "meeting_data"]

    async def process_query(
        self, query: Dict[str, Any], context: Any
    ) -> Dict[str, Any]:
        """Mock query processing"""
        return {
            "sources": [
                {"type": "slack", "name": "Engineering Channel", "messages": 12},
                {"type": "email", "name": "Team Updates", "messages": 5},
            ],
            "data": {
                "recent_discussions": [
                    "Sprint planning for Q4 features",
                    "Bug fixes for mobile app",
                    "API performance optimization",
                ],
                "team_sentiment": "positive",
                "active_threads": 8,
            },
        }

    async def get_health_status(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "connections": {"slack": "connected", "email": "connected"},
        }

    def get_tools(self) -> List[Any]:
        return []  # TODO: Implement actual tools

class MockMemoryEngineModule:
    """Mock Memory Engine module"""

    @property
    def name(self) -> str:
        return "memory_engine"

    @property
    def capabilities(self) -> List[str]:
        return ["user_memory", "team_memory", "context_retrieval", "personalization"]

    async def process_query(
        self, query: Dict[str, Any], context: Any
    ) -> Dict[str, Any]:
        return {
            "sources": [
                {"type": "memory", "name": "User Preferences", "entries": 24},
                {"type": "memory", "name": "Team Context", "entries": 18},
            ],
            "data": {
                "user_context": {
                    "role": "team_lead",
                    "focus_areas": ["mobile_development", "performance"],
                    "communication_style": "detailed",
                },
                "team_context": {
                    "recent_decisions": [
                        "Prioritize bug fixes over new features",
                        "Extend sprint by 2 days for testing",
                    ],
                    "ongoing_projects": ["mobile_app", "api_redesign"],
                },
            },
        }

    async def get_health_status(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "memory_entries": 1247,
            "vector_database": "connected",
        }

    def get_tools(self) -> List[Any]:
        return []

class MockIntegrationHubModule:
    """Mock Integration Hub module"""

    @property
    def name(self) -> str:
        return "integration_hub"

    @property
    def capabilities(self) -> List[str]:
        return ["integration_status", "external_data", "service_monitoring"]

    async def process_query(
        self, query: Dict[str, Any], context: Any
    ) -> Dict[str, Any]:
        return {
            "sources": [
                {"type": "github", "name": "Repository Activity", "events": 15},
                {"type": "jira", "name": "Issue Tracking", "tickets": 8},
            ],
            "data": {
                "integrations_status": {
                    "slack": "healthy",
                    "github": "healthy",
                    "jira": "warning",
                },
                "recent_activity": [
                    "5 pull requests merged today",
                    "3 new issues reported",
                    "2 deployments completed",
                ],
            },
        }

    async def get_health_status(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_integrations": 7,
            "data_freshness": "current",
        }

    def get_tools(self) -> List[Any]:
        return []

class MockTrustLayerModule:
    """Mock Trust Layer module"""

    @property
    def name(self) -> str:
        return "trust_layer"

    @property
    def capabilities(self) -> List[str]:
        return ["confidence_scoring", "source_validation", "fact_checking"]

    async def process_query(
        self, query: Dict[str, Any], context: Any
    ) -> Dict[str, Any]:
        return {
            "sources": [
                {"type": "validation", "name": "Source Credibility", "score": 0.92}
            ],
            "data": {
                "confidence_metrics": {
                    "overall_confidence": 0.89,
                    "source_reliability": 0.94,
                    "data_freshness": 0.85,
                    "cross_validation": 0.88,
                },
                "trust_indicators": [
                    "Multiple source confirmation",
                    "Recent data (<2 hours)",
                    "High source credibility",
                ],
            },
        }

    async def get_health_status(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "validation_rules": "active",
            "confidence_engine": "online",
        }

    def get_tools(self) -> List[Any]:
        return []
