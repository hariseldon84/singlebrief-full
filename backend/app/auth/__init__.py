# Authentication module
from .dependencies import (get_current_active_user, get_current_user,
                           require_role)
from .oauth import get_oauth_provider
from .permissions import PERMISSIONS, check_permission

__all__ = [
    "get_current_user",
    "get_current_active_user",
    "require_role",
    "check_permission",
    "PERMISSIONS",
    "get_oauth_provider",
]
