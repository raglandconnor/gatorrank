from dataclasses import dataclass

import pytest

from app.models.user_roles import USER_ROLE_ADMIN, USER_ROLE_FACULTY, USER_ROLE_STUDENT
from app.policy.roles import (
    PolicyDeniedError,
    can_create_taxonomy_on_miss,
    can_manage_groups,
    can_manage_taxonomy,
    can_moderate_comments,
    require_comment_moderation,
    require_group_management,
    require_taxonomy_create_on_miss,
    require_taxonomy_management,
)


@dataclass
class DummyPrincipal:
    role: str


def test_admin_capabilities_are_allowed():
    admin = DummyPrincipal(role=USER_ROLE_ADMIN)
    assert can_manage_taxonomy(admin) is True
    assert can_create_taxonomy_on_miss(admin) is True
    assert can_moderate_comments(admin) is True
    assert can_manage_groups(admin) is True


@pytest.mark.parametrize("role", [USER_ROLE_STUDENT, USER_ROLE_FACULTY])
def test_non_admin_capabilities_are_denied(role: str):
    principal = DummyPrincipal(role=role)
    assert can_manage_taxonomy(principal) is False
    assert can_create_taxonomy_on_miss(principal) is True
    assert can_moderate_comments(principal) is False
    assert can_manage_groups(principal) is False


def test_unauthenticated_capabilities_are_denied():
    assert can_manage_taxonomy(None) is False
    assert can_create_taxonomy_on_miss(None) is False
    assert can_moderate_comments(None) is False
    assert can_manage_groups(None) is False


@pytest.mark.parametrize(
    "guard",
    [
        require_taxonomy_management,
        require_comment_moderation,
        require_group_management,
    ],
)
def test_admin_passes_policy_guards(guard):
    guard(DummyPrincipal(role=USER_ROLE_ADMIN))


@pytest.mark.parametrize(
    "guard",
    [
        require_taxonomy_management,
        require_comment_moderation,
        require_group_management,
    ],
)
def test_non_admin_fails_policy_guards(guard):
    with pytest.raises(PolicyDeniedError, match="requires admin role"):
        guard(DummyPrincipal(role=USER_ROLE_STUDENT))


def test_taxonomy_create_on_miss_requires_authenticated_principal():
    with pytest.raises(PolicyDeniedError, match="requires authentication"):
        require_taxonomy_create_on_miss(None)


def test_taxonomy_create_on_miss_allows_authenticated_principals():
    require_taxonomy_create_on_miss(DummyPrincipal(role=USER_ROLE_STUDENT))
    require_taxonomy_create_on_miss(DummyPrincipal(role=USER_ROLE_FACULTY))
    require_taxonomy_create_on_miss(DummyPrincipal(role=USER_ROLE_ADMIN))


def test_invalid_role_raises_runtime_error():
    with pytest.raises(RuntimeError, match="Unexpected user role"):
        can_manage_taxonomy(DummyPrincipal(role="invalid"))
