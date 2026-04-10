from dataclasses import dataclass
from typing import Protocol

from app.models.user_roles import USER_ROLE_ADMIN, UserRole, cast_user_role


class PolicyDeniedError(PermissionError):
    """Raised when a principal does not satisfy a policy requirement."""


class PolicyPrincipal(Protocol):
    role: str


@dataclass(frozen=True)
class _PolicyScope:
    label: str


TAXONOMY_MANAGEMENT = _PolicyScope("taxonomy management")
TAXONOMY_CREATE_ON_MISS = _PolicyScope("taxonomy create-on-miss")
COMMENT_MODERATION = _PolicyScope("comment moderation")
GROUP_MANAGEMENT = _PolicyScope("group management")


def _principal_role(principal: PolicyPrincipal | None) -> UserRole | None:
    if principal is None:
        return None
    try:
        return cast_user_role(principal.role)
    except ValueError as exc:
        raise RuntimeError("Unexpected user role in policy principal") from exc


def _has_admin_role(principal: PolicyPrincipal | None) -> bool:
    role = _principal_role(principal)
    return role == USER_ROLE_ADMIN


def _is_authenticated(principal: PolicyPrincipal | None) -> bool:
    return _principal_role(principal) is not None


def _require_scope(principal: PolicyPrincipal | None, scope: _PolicyScope) -> None:
    if _has_admin_role(principal):
        return
    raise PolicyDeniedError(f"{scope.label.capitalize()} requires admin role")


def _require_authenticated_scope(
    principal: PolicyPrincipal | None, scope: _PolicyScope
) -> None:
    if _is_authenticated(principal):
        return
    raise PolicyDeniedError(f"{scope.label.capitalize()} requires authentication")


def can_manage_taxonomy(principal: PolicyPrincipal | None) -> bool:
    """Return whether the principal can manage taxonomy terms."""
    return _has_admin_role(principal)


def can_create_taxonomy_on_miss(principal: PolicyPrincipal | None) -> bool:
    """Return whether the principal can create taxonomy terms through assignment flows."""
    return _is_authenticated(principal)


def can_moderate_comments(principal: PolicyPrincipal | None) -> bool:
    """Return whether the principal can perform comment moderation actions."""
    return _has_admin_role(principal)


def can_manage_groups(principal: PolicyPrincipal | None) -> bool:
    """Return whether the principal can perform group-management actions."""
    return _has_admin_role(principal)


def require_taxonomy_management(principal: PolicyPrincipal | None) -> None:
    """Require permission to manage taxonomy terms."""
    _require_scope(principal, TAXONOMY_MANAGEMENT)


def require_taxonomy_create_on_miss(principal: PolicyPrincipal | None) -> None:
    """Require authenticated principal for taxonomy create-on-miss assignment flows."""
    _require_authenticated_scope(principal, TAXONOMY_CREATE_ON_MISS)


def require_comment_moderation(principal: PolicyPrincipal | None) -> None:
    """Require permission to moderate comments."""
    _require_scope(principal, COMMENT_MODERATION)


def require_group_management(principal: PolicyPrincipal | None) -> None:
    """Require permission to manage groups."""
    _require_scope(principal, GROUP_MANAGEMENT)
