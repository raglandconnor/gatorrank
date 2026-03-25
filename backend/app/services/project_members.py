from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.project import ProjectMember
from app.models.project_roles import cast_project_member_role
from app.models.user import User
from app.schemas.project import ProjectMemberInfo


def _coerce_member_role(value: str):
    try:
        return cast_project_member_role(value)
    except ValueError as exc:
        raise RuntimeError("Unexpected project member role in database") from exc


async def get_members_for_projects(
    db: AsyncSession, project_ids: list[UUID]
) -> dict[UUID, list[ProjectMemberInfo]]:
    if not project_ids:
        return {}

    project_member_cols = getattr(ProjectMember, "__table__").c
    user_cols = getattr(User, "__table__").c
    statement = (
        select(ProjectMember, User)
        .join(User, user_cols.id == project_member_cols.user_id)
        .where(project_member_cols.project_id.in_(project_ids))
        .order_by(
            project_member_cols.project_id.asc(),
            project_member_cols.added_at.asc(),
        )
    )
    result = await db.exec(statement)

    members_by_project: dict[UUID, list[ProjectMemberInfo]] = {
        pid: [] for pid in project_ids
    }
    for member, user in result.all():
        members_by_project[member.project_id].append(
            ProjectMemberInfo(
                user_id=user.id,
                role=_coerce_member_role(member.role),
                full_name=user.full_name,
                profile_picture_url=user.profile_picture_url,
            )
        )

    return members_by_project
