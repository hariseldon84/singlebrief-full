# Authentication module
from .dependencies import (get_current_active_user, get_current_user,
                           require_role)
from .oauth import google_oauth, microsoft_oauth
from .permissions import PERMISSIONS, check_permission

__all__ = [
    "get_current_user",
    "get_current_active_user",
    "require_role",
    "check_permission",
    "PERMISSIONS",
    "google_oauth",
    "microsoft_oauth",
]
