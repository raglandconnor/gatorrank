from typing import Literal, TypeAlias, TypeGuard, cast

USER_ROLE_STUDENT = "student"
USER_ROLE_FACULTY = "faculty"
USER_ROLE_ADMIN = "admin"

UserRole: TypeAlias = Literal["student", "faculty", "admin"]

USER_ROLES = frozenset[UserRole](
    {
        USER_ROLE_STUDENT,
        USER_ROLE_FACULTY,
        USER_ROLE_ADMIN,
    }
)


def normalize_user_role(value: str) -> str:
    return value.strip().lower()


def is_user_role(value: str) -> TypeGuard[UserRole]:
    return value in USER_ROLES


def cast_user_role(value: str) -> UserRole:
    normalized = normalize_user_role(value)
    if not is_user_role(normalized):
        raise ValueError(f"Unexpected user role: {value}")
    return cast(UserRole, normalized)
