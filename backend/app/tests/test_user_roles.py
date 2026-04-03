import pytest

from app.models.user_roles import (
    USER_ROLE_ADMIN,
    USER_ROLE_FACULTY,
    USER_ROLE_STUDENT,
    USER_ROLES,
    cast_user_role,
    is_user_role,
    normalize_user_role,
)


def test_user_roles_set_is_expected():
    assert USER_ROLES == frozenset(
        {USER_ROLE_STUDENT, USER_ROLE_FACULTY, USER_ROLE_ADMIN}
    )


def test_normalize_user_role_trims_and_lowercases():
    assert normalize_user_role("  AdMiN  ") == USER_ROLE_ADMIN


def test_is_user_role_accepts_only_known_values():
    assert is_user_role(USER_ROLE_STUDENT) is True
    assert is_user_role(USER_ROLE_FACULTY) is True
    assert is_user_role(USER_ROLE_ADMIN) is True
    assert is_user_role("owner") is False


@pytest.mark.parametrize(
    "value,expected",
    [
        ("student", USER_ROLE_STUDENT),
        (" FACULTY ", USER_ROLE_FACULTY),
        ("AdMiN", USER_ROLE_ADMIN),
    ],
)
def test_cast_user_role_accepts_known_roles(value: str, expected: str):
    assert cast_user_role(value) == expected


def test_cast_user_role_rejects_unknown_value():
    with pytest.raises(ValueError, match="Unexpected user role"):
        cast_user_role("super_admin")
