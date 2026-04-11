from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps.auth import get_current_user, get_current_user_optional
from app.api.deps.policy import raise_policy_forbidden
from app.db.database import get_db
from app.models.user import User
from app.models.user_roles import USER_ROLE_ADMIN
from app.schemas.comment import CommentCreateRequest, CommentResponse
from app.services.comment import (
    CommentForbiddenError,
    CommentNotFoundError,
    CommentProjectNotFoundError,
    CommentService,
)
from app.services.comment_like import CommentLikeService

router = APIRouter()


@router.get(
    "/projects/{project_id}/comments",
    summary="List comments for a project",
    response_model=list[CommentResponse],
)
async def list_comments(
    project_id: UUID,
    sort: Literal["most_liked", "oldest", "newest"] = Query(
        default="most_liked", description="Sort order for comments"
    ),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    service = CommentService(db)
    try:
        viewer_id = current_user.id if current_user else None
        return await service.list_comments(
            project_id=project_id, viewer_id=viewer_id, sort_by=sort
        )
    except CommentProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")


@router.post(
    "/projects/{project_id}/comments",
    summary="Create a comment",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    project_id: UUID,
    payload: CommentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CommentService(db)
    try:
        return await service.create_comment(
            project_id=project_id, author_id=current_user.id, data=payload
        )
    except CommentProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")


@router.delete(
    "/comments/{comment_id}",
    summary="Delete own comment",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_comment(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CommentService(db)
    try:
        is_admin = current_user.role == USER_ROLE_ADMIN
        await service.delete_comment(
            comment_id=comment_id, actor_id=current_user.id, is_admin=is_admin
        )
    except CommentNotFoundError:
        raise HTTPException(status_code=404, detail="Comment not found")
    except CommentForbiddenError:
        raise HTTPException(status_code=403, detail="Forbidden to delete comment")
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/comments/{comment_id}/moderate",
    summary="Admin moderation for a comment",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def moderate_comment(
    comment_id: UUID,
    state: Literal["visible", "hidden"],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != USER_ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Admin permissions required")

    service = CommentService(db)
    try:
        await service.moderate_comment(comment_id=comment_id, new_state=state)
    except CommentNotFoundError:
        raise HTTPException(status_code=404, detail="Comment not found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/comments/{comment_id}/like",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Like a comment",
)
async def like_comment(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CommentLikeService(db)
    try:
        await service.add_like(comment_id=comment_id, user_id=current_user.id)
    except CommentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/comments/{comment_id}/like",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unlike a comment",
)
async def unlike_comment(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CommentLikeService(db)
    try:
        await service.remove_like(comment_id=comment_id, user_id=current_user.id)
    except CommentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
