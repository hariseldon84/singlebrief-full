"""Integration Hub Service for SingleBrief.

This module implements the core Integration Hub framework for managing
external service connectors, health monitoring, rate limiting, and configuration.
"""

import asyncio
import logging
import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import semver
import jsonschema
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, update
from sqlalchemy.orm import selectinload

from app.models.integration import (
    Connector, ConnectorInstallation, ConnectorHealthCheck, 
    RateLimit, ConfigurationTemplate, Integration, OAuthToken
)
from app.models.user import User, Organization
from app.core.database import get_async_session

logger = logging.getLogger(__name__)


@dataclass
class ConnectorMetrics:
    """Metrics for a connector installation."""
    total_api_calls: int
    success_rate: float
    error_rate: float
    avg_response_time: float
    current_rate_limit_usage: int
    health_status: str
    last_health_check: Optional[datetime]


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""
    status: str  # healthy, degraded, unhealthy, unknown
    message: str
    response_time_ms: Optional[int]
    details: Dict[str, Any]
    recommendations: List[str]


class IntegrationHubService:
    """Service for managing the Integration Hub framework."""
    
    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
        self.rate_limit_cache = {}  # Cache for rate limiting
        self.health_check_interval = 300  # 5 minutes
        self.max_retry_attempts = 3
        self.retry_backoff_factor = 2.0
        
    async def register_connector(
        self,
        connector_type: str,
        name: str,
        version: str,
        developer: str,
        capabilities: List[str],
        config_schema: Dict[str, Any],
        **kwargs
    ) -> Connector:
        """Register a new connector in the marketplace.
        
        Args:
            connector_type: Type identifier (e.g., 'slack', 'teams')
            name: Human-readable name
            version: Semantic version
            developer: Developer/organization name
            capabilities: List of connector capabilities
            config_schema: JSON schema for configuration
            **kwargs: Additional optional parameters
            
        Returns:
            Created Connector instance
        """
        session = self.session or await get_async_session().__anext__()
        
        try:
            # Validate version format
            if not self._is_valid_semver(version):
                raise ValueError(f"Invalid semantic version: {version}")
            
            # Validate configuration schema
            if not self._validate_config_schema(config_schema):
                raise ValueError("Invalid configuration schema")
            
            # Check for existing connector with same type and version
            existing = await self._get_connector_by_type_version(session, connector_type, version)
            if existing:
                raise ValueError(f"Connector {connector_type} v{version} already exists")
            
            # Create connector
            connector = Connector(
                connector_type=connector_type,
                name=name,
                version=version,
                developer=developer,
                capabilities=capabilities,
                required_scopes=kwargs.get('required_scopes', []),
                supported_auth_types=kwargs.get('supported_auth_types', ['oauth2']),
                config_schema=config_schema,
                default_config=kwargs.get('default_config', {}),
                description=kwargs.get('description'),
                min_framework_version=kwargs.get('min_framework_version', '1.0.0'),
                homepage_url=kwargs.get('homepage_url'),
                documentation_url=kwargs.get('documentation_url'),
                support_url=kwargs.get('support_url'),
                default_rate_limit_hour=kwargs.get('default_rate_limit_hour'),
                default_rate_limit_day=kwargs.get('default_rate_limit_day'),
                burst_limit=kwargs.get('burst_limit'),
                is_official=kwargs.get('is_official', False),
                is_verified=kwargs.get('is_verified', False),
                package_url=kwargs.get('package_url'),
                install_script=kwargs.get('install_script'),
                dependencies=kwargs.get('dependencies', []),
                conflicts=kwargs.get('conflicts', []),
                published_at=datetime.now(timezone.utc)
            )
            
            # Generate checksum if package URL provided
            if connector.package_url:
                connector.checksum = await self._generate_package_checksum(connector.package_url)
            
            session.add(connector)
            await session.commit()
            await session.refresh(connector)
            
            logger.info(f"Registered connector: {connector_type} v{version}")
            return connector
            
        except Exception as e:
            logger.error(f"Error registering connector: {e}")
            await session.rollback()
            raise
        finally:
            if not self.session:
                await session.close()
    
    async def install_connector(
        self,
        connector_id: str,
        organization_id: str,
        user_id: str,
        installation_config: Dict[str, Any],
        environment: str = "production"
    ) -> ConnectorInstallation:
        """Install a connector for an organization.
        
        Args:
            connector_id: ID of the connector to install
            organization_id: Organization ID
            user_id: ID of user performing installation
            installation_config: Organization-specific configuration
            environment: Installation environment
            
        Returns:
            Created ConnectorInstallation instance
        """
        session = self.session or await get_async_session().__anext__()
        
        try:
            # Get connector and validate
            connector = await self._get_connector_by_id(session, connector_id)
            if not connector:
                raise ValueError(f"Connector {connector_id} not found")
            
            # Check for existing installation
            existing = await self._get_installation_by_connector_org(
                session, connector_id, organization_id
            )
            if existing:
                raise ValueError(f"Connector already installed in organization")
            
            # Validate installation configuration against schema
            await self._validate_installation_config(connector, installation_config)
            
            # Check dependencies
            await self._validate_connector_dependencies(session, connector, organization_id)
            
            # Create installation
            installation = ConnectorInstallation(
                connector_id=connector_id,
                organization_id=organization_id,
                installed_by_user_id=user_id,
                installation_config=installation_config,
                environment=environment,
                status="installed",
                health_status="unknown"
            )
            
            session.add(installation)
            await session.commit()
            await session.refresh(installation)
            
            # Set up default rate limits
            await self._setup_default_rate_limits(session, installation, connector)
            
            # Schedule initial health check
            await self._schedule_health_check(session, installation)
            
            logger.info(f"Installed connector {connector.connector_type} for org {organization_id}")
            return installation
            
        except Exception as e:
            logger.error(f"Error installing connector: {e}")
            await session.rollback()
            raise
        finally:
            if not self.session:
                await session.close()
    
    async def perform_health_check(
        self,
        installation_id: str,
        check_type: str = "connectivity"
    ) -> HealthCheckResult:
        """Perform a health check on a connector installation.
        
        Args:
            installation_id: Installation ID to check
            check_type: Type of health check to perform
            
        Returns:
            HealthCheckResult with status and metrics
        """
        session = self.session or await get_async_session().__anext__()
        
        try:
            # Get installation with connector
            installation = await self._get_installation_with_connector(session, installation_id)
            if not installation:
                raise ValueError(f"Installation {installation_id} not found")
            
            # Perform the actual health check
            start_time = time.time()
            check_result = await self._execute_health_check(installation, check_type)
            response_time = int((time.time() - start_time) * 1000)
            
            # Create health check record
            health_check = ConnectorHealthCheck(
                connector_id=installation.connector_id,
                organization_id=installation.organization_id,
                check_type=check_type,
                status=check_result.status,
                response_time_ms=response_time,
                success_rate=check_result.details.get('success_rate'),
                error_rate=check_result.details.get('error_rate'),
                message=check_result.message,
                details=check_result.details,
                recommendations=check_result.recommendations,
                checked_at=datetime.now(timezone.utc),
                next_check_at=datetime.now(timezone.utc) + timedelta(seconds=self.health_check_interval)
            )
            
            session.add(health_check)
            
            # Update installation health status
            installation.health_status = check_result.status
            installation.last_health_check = health_check.checked_at
            
            await session.commit()
            
            logger.info(f"Health check completed for {installation_id}: {check_result.status}")
            return check_result
            
        except Exception as e:
            logger.error(f"Error performing health check: {e}")
            await session.rollback()
            raise
        finally:
            if not self.session:
                await session.close()
    
    async def check_rate_limit(
        self,
        installation_id: str,
        limit_type: str = "requests_per_hour"
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if a request is within rate limits.
        
        Args:
            installation_id: Installation ID
            limit_type: Type of rate limit to check
            
        Returns:
            Tuple of (is_allowed, limit_info)
        """
        session = self.session or await get_async_session().__anext__()
        
        try:
            # Get rate limit configuration
            rate_limit = await self._get_rate_limit(session, installation_id, limit_type)
            if not rate_limit:
                return True, {"message": "No rate limit configured"}
            
            current_time = datetime.now(timezone.utc)
            
            # Check if window has expired
            if current_time >= rate_limit.window_start + timedelta(seconds=rate_limit.window_seconds):
                # Reset window
                rate_limit.window_start = current_time
                rate_limit.current_usage = 0
            
            # Check if within limit
            is_allowed = rate_limit.current_usage < rate_limit.limit_value
            
            if is_allowed:
                # Increment usage
                rate_limit.current_usage += 1
                rate_limit.last_request_at = current_time
            else:
                # Track violation
                rate_limit.violations_count += 1
                rate_limit.consecutive_violations += 1
                rate_limit.last_violation_at = current_time
                
                # Update status based on violations
                if rate_limit.consecutive_violations >= 5:
                    rate_limit.status = "critical"
                elif rate_limit.consecutive_violations >= 3:
                    rate_limit.status = "warning"
            
            await session.commit()
            
            limit_info = {
                "limit_value": rate_limit.limit_value,
                "current_usage": rate_limit.current_usage,
                "window_seconds": rate_limit.window_seconds,
                "window_start": rate_limit.window_start.isoformat(),
                "status": rate_limit.status,
                "consecutive_violations": rate_limit.consecutive_violations
            }
            
            return is_allowed, limit_info
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return False, {"error": str(e)}
        finally:
            if not self.session:
                await session.close()
    
    async def update_connector(
        self,
        connector_id: str,
        new_version: str,
        update_data: Dict[str, Any]
    ) -> Connector:
        """Update a connector to a new version.
        
        Args:
            connector_id: Connector ID to update
            new_version: New version number
            update_data: Updated connector data
            
        Returns:
            Updated Connector instance
        """
        session = self.session or await get_async_session().__anext__()
        
        try:
            connector = await self._get_connector_by_id(session, connector_id)
            if not connector:
                raise ValueError(f"Connector {connector_id} not found")
            
            # Validate new version
            if not self._is_valid_semver(new_version):
                raise ValueError(f"Invalid semantic version: {new_version}")
            
            # Check if new version is higher
            if not self._is_version_higher(new_version, connector.version):
                raise ValueError(f"New version {new_version} must be higher than current {connector.version}")
            
            # Update connector fields
            for field, value in update_data.items():
                if hasattr(connector, field):
                    setattr(connector, field, value)
            
            connector.version = new_version
            connector.updated_at = datetime.now(timezone.utc)
            
            # Generate new checksum if package URL updated
            if 'package_url' in update_data and update_data['package_url']:
                connector.checksum = await self._generate_package_checksum(update_data['package_url'])
            
            await session.commit()
            
            # Schedule updates for installations
            await self._schedule_installation_updates(session, connector)
            
            logger.info(f"Updated connector {connector.connector_type} to v{new_version}")
            return connector
            
        except Exception as e:
            logger.error(f"Error updating connector: {e}")
            await session.rollback()
            raise
        finally:
            if not self.session:
                await session.close()
    
    async def get_connector_metrics(
        self,
        installation_id: str,
        days: int = 7
    ) -> ConnectorMetrics:
        """Get metrics for a connector installation.
        
        Args:
            installation_id: Installation ID
            days: Number of days to calculate metrics for
            
        Returns:
            ConnectorMetrics with performance data
        """
        session = self.session or await get_async_session().__anext__()
        
        try:
            installation = await self._get_installation_with_connector(session, installation_id)
            if not installation:
                raise ValueError(f"Installation {installation_id} not found")
            
            # Calculate metrics from logs and health checks
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Get health check metrics
            health_metrics = await self._calculate_health_metrics(session, installation, cutoff_date)
            
            # Get rate limit usage
            rate_limit_usage = await self._get_rate_limit_usage(session, installation_id)
            
            return ConnectorMetrics(
                total_api_calls=installation.total_api_calls,
                success_rate=health_metrics.get('success_rate', 0.0),
                error_rate=health_metrics.get('error_rate', 0.0),
                avg_response_time=health_metrics.get('avg_response_time', 0.0),
                current_rate_limit_usage=rate_limit_usage,
                health_status=installation.health_status,
                last_health_check=installation.last_health_check
            )
            
        except Exception as e:
            logger.error(f"Error getting connector metrics: {e}")
            raise
        finally:
            if not self.session:
                await session.close()
    
    async def create_configuration_template(
        self,
        connector_id: str,
        name: str,
        use_case: str,
        template_config: Dict[str, Any],
        created_by_user_id: str,
        **kwargs
    ) -> ConfigurationTemplate:
        """Create a configuration template for a connector.
        
        Args:
            connector_id: Connector ID
            name: Template name
            use_case: Template use case
            template_config: Template configuration
            created_by_user_id: User creating the template
            **kwargs: Additional template parameters
            
        Returns:
            Created ConfigurationTemplate instance
        """
        session = self.session or await get_async_session().__anext__()
        
        try:
            # Validate connector exists
            connector = await self._get_connector_by_id(session, connector_id)
            if not connector:
                raise ValueError(f"Connector {connector_id} not found")
            
            # Validate template configuration against connector schema
            await self._validate_template_config(connector, template_config)
            
            template = ConfigurationTemplate(
                connector_id=connector_id,
                name=name,
                use_case=use_case,
                template_config=template_config,
                created_by_user_id=created_by_user_id,
                description=kwargs.get('description'),
                category=kwargs.get('category', 'integration'),
                required_variables=kwargs.get('required_variables', []),
                optional_variables=kwargs.get('optional_variables', []),
                validation_rules=kwargs.get('validation_rules'),
                dependencies=kwargs.get('dependencies', []),
                organization_id=kwargs.get('organization_id'),
                visibility=kwargs.get('visibility', 'public'),
                is_official=kwargs.get('is_official', False),
                is_featured=kwargs.get('is_featured', False)
            )
            
            session.add(template)
            await session.commit()
            await session.refresh(template)
            
            logger.info(f"Created configuration template: {name} for connector {connector_id}")
            return template
            
        except Exception as e:
            logger.error(f"Error creating configuration template: {e}")
            await session.rollback()
            raise
        finally:
            if not self.session:
                await session.close()
    
    # Helper methods
    
    async def _get_connector_by_id(self, session: AsyncSession, connector_id: str) -> Optional[Connector]:
        """Get connector by ID."""
        query = select(Connector).where(Connector.id == connector_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_connector_by_type_version(
        self, 
        session: AsyncSession, 
        connector_type: str, 
        version: str
    ) -> Optional[Connector]:
        """Get connector by type and version."""
        query = select(Connector).where(
            and_(
                Connector.connector_type == connector_type,
                Connector.version == version
            )
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_installation_by_connector_org(
        self, 
        session: AsyncSession, 
        connector_id: str, 
        organization_id: str
    ) -> Optional[ConnectorInstallation]:
        """Get installation by connector and organization."""
        query = select(ConnectorInstallation).where(
            and_(
                ConnectorInstallation.connector_id == connector_id,
                ConnectorInstallation.organization_id == organization_id
            )
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_installation_with_connector(
        self, 
        session: AsyncSession, 
        installation_id: str
    ) -> Optional[ConnectorInstallation]:
        """Get installation with connector relationship loaded."""
        query = select(ConnectorInstallation).options(
            selectinload(ConnectorInstallation.connector)
        ).where(ConnectorInstallation.id == installation_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_rate_limit(
        self, 
        session: AsyncSession, 
        installation_id: str, 
        limit_type: str
    ) -> Optional[RateLimit]:
        """Get rate limit for installation and type."""
        query = select(RateLimit).where(
            and_(
                RateLimit.connector_installation_id == installation_id,
                RateLimit.limit_type == limit_type,
                RateLimit.is_active == True
            )
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    def _is_valid_semver(self, version: str) -> bool:
        """Validate semantic version format."""
        try:
            semver.VersionInfo.parse(version)
            return True
        except ValueError:
            return False
    
    def _is_version_higher(self, new_version: str, current_version: str) -> bool:
        """Check if new version is higher than current."""
        try:
            return semver.compare(new_version, current_version) > 0
        except ValueError:
            return False
    
    def _validate_config_schema(self, schema: Dict[str, Any]) -> bool:
        """Validate JSON schema format."""
        try:
            # Basic validation - in production, use more comprehensive validation
            required_fields = ['type', 'properties']
            return all(field in schema for field in required_fields)
        except Exception:
            return False
    
    async def _validate_installation_config(
        self, 
        connector: Connector, 
        config: Dict[str, Any]
    ) -> None:
        """Validate installation configuration against connector schema."""
        try:
            jsonschema.validate(instance=config, schema=connector.config_schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Configuration validation failed: {e.message}")
    
    async def _validate_template_config(
        self, 
        connector: Connector, 
        config: Dict[str, Any]
    ) -> None:
        """Validate template configuration against connector schema."""
        try:
            jsonschema.validate(instance=config, schema=connector.config_schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Template configuration validation failed: {e.message}")
    
    async def _validate_connector_dependencies(
        self, 
        session: AsyncSession, 
        connector: Connector, 
        organization_id: str
    ) -> None:
        """Validate that connector dependencies are met."""
        if not connector.dependencies:
            return
        
        for dep_type in connector.dependencies:
            # Check if dependency connector is installed
            dep_query = select(ConnectorInstallation).join(Connector).where(
                and_(
                    Connector.connector_type == dep_type,
                    ConnectorInstallation.organization_id == organization_id,
                    ConnectorInstallation.status == "installed"
                )
            )
            result = await session.execute(dep_query)
            if not result.scalar_one_or_none():
                raise ValueError(f"Missing dependency: {dep_type}")
    
    async def _setup_default_rate_limits(
        self, 
        session: AsyncSession, 
        installation: ConnectorInstallation, 
        connector: Connector
    ) -> None:
        """Set up default rate limits for installation."""
        current_time = datetime.now(timezone.utc)
        
        # Hourly rate limit
        if connector.default_rate_limit_hour:
            hourly_limit = RateLimit(
                connector_installation_id=installation.id,
                limit_type="requests_per_hour",
                limit_value=connector.default_rate_limit_hour,
                burst_limit=connector.burst_limit,
                window_seconds=3600,
                window_start=current_time
            )
            session.add(hourly_limit)
        
        # Daily rate limit
        if connector.default_rate_limit_day:
            daily_limit = RateLimit(
                connector_installation_id=installation.id,
                limit_type="requests_per_day",
                limit_value=connector.default_rate_limit_day,
                window_seconds=86400,
                window_start=current_time
            )
            session.add(daily_limit)
    
    async def _schedule_health_check(
        self, 
        session: AsyncSession, 
        installation: ConnectorInstallation
    ) -> None:
        """Schedule initial health check for installation."""
        # In production, this would integrate with a task queue like Celery
        # For now, we'll just create a placeholder health check
        placeholder_check = ConnectorHealthCheck(
            connector_id=installation.connector_id,
            organization_id=installation.organization_id,
            check_type="connectivity",
            status="unknown",
            message="Health check scheduled",
            checked_at=datetime.now(timezone.utc),
            next_check_at=datetime.now(timezone.utc) + timedelta(seconds=self.health_check_interval)
        )
        session.add(placeholder_check)
    
    async def _execute_health_check(
        self, 
        installation: ConnectorInstallation, 
        check_type: str
    ) -> HealthCheckResult:
        """Execute the actual health check logic."""
        # This is a simplified implementation
        # In production, this would make actual API calls to external services
        
        try:
            if check_type == "connectivity":
                # Simulate connectivity check
                await asyncio.sleep(0.1)  # Simulate network call
                return HealthCheckResult(
                    status="healthy",
                    message="Connectivity check passed",
                    response_time_ms=100,
                    details={"endpoint_reachable": True, "success_rate": 0.95},
                    recommendations=[]
                )
            elif check_type == "authentication":
                # Simulate auth check
                return HealthCheckResult(
                    status="healthy",
                    message="Authentication check passed",
                    response_time_ms=150,
                    details={"token_valid": True, "expires_in": 3600},
                    recommendations=[]
                )
            else:
                return HealthCheckResult(
                    status="unknown",
                    message=f"Unknown check type: {check_type}",
                    response_time_ms=None,
                    details={},
                    recommendations=["Use supported check types"]
                )
        except Exception as e:
            return HealthCheckResult(
                status="unhealthy",
                message=f"Health check failed: {str(e)}",
                response_time_ms=None,
                details={"error": str(e)},
                recommendations=["Check configuration and network connectivity"]
            )
    
    async def _calculate_health_metrics(
        self, 
        session: AsyncSession, 
        installation: ConnectorInstallation, 
        cutoff_date: datetime
    ) -> Dict[str, float]:
        """Calculate health metrics for an installation."""
        # Get recent health checks
        health_query = select(ConnectorHealthCheck).where(
            and_(
                ConnectorHealthCheck.connector_id == installation.connector_id,
                ConnectorHealthCheck.organization_id == installation.organization_id,
                ConnectorHealthCheck.checked_at >= cutoff_date
            )
        )
        result = await session.execute(health_query)
        health_checks = result.scalars().all()
        
        if not health_checks:
            return {"success_rate": 0.0, "error_rate": 0.0, "avg_response_time": 0.0}
        
        # Calculate metrics
        healthy_checks = sum(1 for hc in health_checks if hc.status == "healthy")
        total_checks = len(health_checks)
        success_rate = healthy_checks / total_checks
        error_rate = 1.0 - success_rate
        
        # Average response time (excluding None values)
        response_times = [hc.response_time_ms for hc in health_checks if hc.response_time_ms is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        
        return {
            "success_rate": success_rate,
            "error_rate": error_rate,
            "avg_response_time": avg_response_time
        }
    
    async def _get_rate_limit_usage(
        self, 
        session: AsyncSession, 
        installation_id: str
    ) -> int:
        """Get current rate limit usage for installation."""
        rate_limit = await self._get_rate_limit(session, installation_id, "requests_per_hour")
        return rate_limit.current_usage if rate_limit else 0
    
    async def _schedule_installation_updates(
        self, 
        session: AsyncSession, 
        connector: Connector
    ) -> None:
        """Schedule updates for installations of this connector."""
        # Get all installations with auto-update enabled
        installations_query = select(ConnectorInstallation).where(
            and_(
                ConnectorInstallation.connector_id == connector.id,
                ConnectorInstallation.auto_update == True,
                ConnectorInstallation.status == "installed"
            )
        )
        result = await session.execute(installations_query)
        installations = result.scalars().all()
        
        # Mark installations as having pending updates
        for installation in installations:
            installation.pending_update_version = connector.version
            installation.last_update_check = datetime.now(timezone.utc)
    
    async def _generate_package_checksum(self, package_url: str) -> str:
        """Generate checksum for package verification."""
        # This is a placeholder implementation
        # In production, this would download and hash the actual package
        return hashlib.sha256(package_url.encode()).hexdigest()


# Singleton instance for easy access
integration_hub_service = IntegrationHubService()