from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps.auth import get_current_user_id_optional
from app.db.database import get_db
from app.schemas.project import ProjectDetailResponse
from app.services.project import ProjectService

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
