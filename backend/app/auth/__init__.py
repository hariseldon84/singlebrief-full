# Authentication module
from .dependencies import get_current_user, get_current_active_user, require_role
from .permissions import check_permission, PERMISSIONS
from .oauth import google_oauth, microsoft_oauth

__all__ = [
    "get_current_user",
    "get_current_active_user", 
    "require_role",
    "check_permission",
    "PERMISSIONS",
    "google_oauth",
    "microsoft_oauth"
]