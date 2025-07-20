"""
Role-based access control and permissions system
"""

from typing import Any, Dict, List, Optional, Tuple, Set

from enum import Enum

from app.models.user import User, UserRole

class Permission(str, Enum):
    """System permissions"""

    # User management
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"

    # Organization management
    ORG_READ = "org:read"
    ORG_WRITE = "org:write"
    ORG_DELETE = "org:delete"
    ORG_ADMIN = "org:admin"

    # Team management
    TEAM_READ = "team:read"
    TEAM_WRITE = "team:write"
    TEAM_DELETE = "team:delete"
    TEAM_ADMIN = "team:admin"
    TEAM_INVITE = "team:invite"

    # Memory and data
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    MEMORY_DELETE = "memory:delete"
    MEMORY_ADMIN = "memory:admin"

    # Intelligence and queries
    QUERY_CREATE = "query:create"
    QUERY_READ = "query:read"
    QUERY_ADMIN = "query:admin"

    # Brief and reports
    BRIEF_READ = "brief:read"
    BRIEF_CREATE = "brief:create"
    BRIEF_ADMIN = "brief:admin"

    # Integration management
    INTEGRATION_READ = "integration:read"
    INTEGRATION_WRITE = "integration:write"
    INTEGRATION_ADMIN = "integration:admin"

    # Analytics and monitoring
    ANALYTICS_READ = "analytics:read"
    ANALYTICS_ADMIN = "analytics:admin"

    # System administration
    SYSTEM_ADMIN = "system:admin"
    AUDIT_READ = "audit:read"
    SETTINGS_WRITE = "settings:write"

# Role-based permission mapping
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.ADMIN: {
        # Full system access
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.USER_DELETE,
        Permission.ORG_READ,
        Permission.ORG_WRITE,
        Permission.ORG_DELETE,
        Permission.ORG_ADMIN,
        Permission.TEAM_READ,
        Permission.TEAM_WRITE,
        Permission.TEAM_DELETE,
        Permission.TEAM_ADMIN,
        Permission.TEAM_INVITE,
        Permission.MEMORY_READ,
        Permission.MEMORY_WRITE,
        Permission.MEMORY_DELETE,
        Permission.MEMORY_ADMIN,
        Permission.QUERY_CREATE,
        Permission.QUERY_READ,
        Permission.QUERY_ADMIN,
        Permission.BRIEF_READ,
        Permission.BRIEF_CREATE,
        Permission.BRIEF_ADMIN,
        Permission.INTEGRATION_READ,
        Permission.INTEGRATION_WRITE,
        Permission.INTEGRATION_ADMIN,
        Permission.ANALYTICS_READ,
        Permission.ANALYTICS_ADMIN,
        Permission.SYSTEM_ADMIN,
        Permission.AUDIT_READ,
        Permission.SETTINGS_WRITE,
    },
    UserRole.MANAGER: {
        # Manager permissions
        Permission.USER_READ,
        Permission.USER_WRITE,  # For team members
        Permission.ORG_READ,
        Permission.TEAM_READ,
        Permission.TEAM_WRITE,
        Permission.TEAM_ADMIN,
        Permission.TEAM_INVITE,
        Permission.MEMORY_READ,
        Permission.MEMORY_WRITE,
        Permission.QUERY_CREATE,
        Permission.QUERY_READ,
        Permission.QUERY_ADMIN,
        Permission.BRIEF_READ,
        Permission.BRIEF_CREATE,
        Permission.BRIEF_ADMIN,
        Permission.INTEGRATION_READ,
        Permission.INTEGRATION_WRITE,
        Permission.ANALYTICS_READ,
    },
    UserRole.TEAM_MEMBER: {
        # Basic user permissions
        Permission.USER_READ,  # Own profile only
        Permission.ORG_READ,  # Read organization info
        Permission.TEAM_READ,  # Read own teams
        Permission.MEMORY_READ,
        Permission.MEMORY_WRITE,  # Own memory only
        Permission.QUERY_CREATE,
        Permission.QUERY_READ,  # Own queries
        Permission.BRIEF_READ,  # Own briefs
        Permission.BRIEF_CREATE,
        Permission.INTEGRATION_READ,  # Read available integrations
    },
}

class PermissionChecker:
    """Permission checking utilities"""

    def __init__(self, user: User):
        self.user = user
        self.permissions = ROLE_PERMISSIONS.get(user.role, set())

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission"""
        return permission in self.permissions

    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions"""
        return any(perm in self.permissions for perm in permissions)

    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if user has all of the specified permissions"""
        return all(perm in self.permissions for perm in permissions)

    def can_access_user(self, target_user_id: str) -> bool:
        """Check if user can access another user's data"""
        # Admins can access all users
        if self.user.role == UserRole.ADMIN:
            return True

        # Users can always access their own data
        if str(self.user.id) == target_user_id:
            return True

        # Managers can access team members (would need additional team check)
        if self.user.role == UserRole.MANAGER:
            # TODO: Implement team membership check
            return True

        return False

    def can_access_organization(self, org_id: str) -> bool:
        """Check if user can access organization data"""
        # Must be member of the organization
        return str(self.user.organization_id) == org_id

    def can_access_team(self, team_id: str) -> bool:
        """Check if user can access team data"""
        # Check if user is member of the team
        team_ids = [str(team.id) for team in self.user.teams]
        return team_id in team_ids

    def can_manage_team(self, team_id: str) -> bool:
        """Check if user can manage a specific team"""
        if not self.has_permission(Permission.TEAM_ADMIN):
            return False

        # Admins can manage all teams in their org
        if self.user.role == UserRole.ADMIN:
            return self.can_access_team(team_id)

        # Managers need to be team admins or team creators
        # TODO: Implement team role checking
        return self.can_access_team(team_id)

def check_permission(user: User, permission: Permission) -> bool:
    """Check if user has permission"""
    checker = PermissionChecker(user)
    return checker.has_permission(permission)

def require_permission(permission: Permission):
    """Decorator factory for requiring specific permissions"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user from function parameters or dependencies
            user = kwargs.get("current_user") or args[0] if args else None
            if not user or not isinstance(user, User):
                raise ValueError("User not found in function parameters")

            if not check_permission(user, permission):
                from fastapi import HTTPException, status

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {permission.value}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator

def get_user_permissions(user: User) -> List[str]:
    """Get list of permissions for a user"""
    permissions = ROLE_PERMISSIONS.get(user.role, set())
    return [perm.value for perm in permissions]

def can_user_access_resource(
    user: User, resource_type: str, resource_id: str, action: str = "read"
) -> bool:
    """Generic resource access check"""
    checker = PermissionChecker(user)

    # Map resource types to permission checks
    if resource_type == "user":
        return checker.can_access_user(resource_id)
    elif resource_type == "organization":
        return checker.can_access_organization(resource_id)
    elif resource_type == "team":
        return checker.can_access_team(resource_id)

    return False

# Export permission constants for easy access
PERMISSIONS = Permission
