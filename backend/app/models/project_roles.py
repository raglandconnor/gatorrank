from typing import Literal, TypeAlias, TypeGuard, cast

PROJECT_ROLE_OWNER = "owner"
PROJECT_ROLE_MAINTAINER = "maintainer"
PROJECT_ROLE_CONTRIBUTOR = "contributor"

ProjectMemberRole: TypeAlias = Literal[
    "owner",
    "maintainer",
    "contributor",
]
ProjectMemberWritableRole: TypeAlias = Literal[
    "maintainer",
    "contributor",
]

PROJECT_MEMBER_ROLES = frozenset[ProjectMemberRole](
    {
        PROJECT_ROLE_OWNER,
        PROJECT_ROLE_MAINTAINER,
        PROJECT_ROLE_CONTRIBUTOR,
    }
)


def is_project_member_role(value: str) -> TypeGuard[ProjectMemberRole]:
    return value in PROJECT_MEMBER_ROLES


def cast_project_member_role(value: str) -> ProjectMemberRole:
    if not is_project_member_role(value):
        raise ValueError(f"Unexpected project member role: {value}")
    return cast(ProjectMemberRole, value)
