from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps.auth import get_current_user_id_optional
from app.db.database import get_db
from app.schemas.project import ProjectDetailResponse, ProjectListResponse
from app.services.project import CursorError, ProjectService

router = APIRouter()


@router.get(
    "/projects/{project_id}",
    summary="Get project detail",
    description="Return project details if visible to the current requester",
    response_model=ProjectDetailResponse,
)
async def get_project_detail(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID | None = Depends(get_current_user_id_optional),
) -> ProjectDetailResponse:
    service = ProjectService(db)
    project = await service.get_project_detail(project_id, current_user_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get(
    "/projects",
    summary="List projects",
    description="Return published projects feed with cursor pagination",
    response_model=ProjectListResponse,
)
async def list_projects(
    limit: int = 20,
    cursor: str | None = None,
    sort: Literal["top", "new"] = "top",
    db: AsyncSession = Depends(get_db),
) -> ProjectListResponse:
    service = ProjectService(db)
    try:
        return await service.list_projects(sort=sort, limit=limit, cursor=cursor)
    except CursorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
