from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps.auth import get_current_user
from app.api.deps.auth import get_current_user_optional
from app.api.deps.policy import require_policy
from app.db.database import get_db
from app.models.user import User
from app.policy.roles import require_comment_moderation
from app.schemas.comment import (
    CommentCreateRequest,
    CommentModerationRequest,
    CommentResponse,
)
from app.services.comment import (
    COMMENT_LIST_HARD_CAP,
    CommentForbiddenError,
    CommentProjectNotFoundError,
    CommentService,
)
from app.services.comment_like import CommentLikeService, CommentNotFoundError

router = APIRouter()


@router.get(
    "/projects/{project_id}/comments",
    summary="List project comments",
    description=(
        "Return the project's comments as a non-paginated v1 list. Only comments for "
        "published, non-deleted projects are exposed. Results are capped server-side "
        f"at {COMMENT_LIST_HARD_CAP} comments per request. Default sorting is by most liked."
    ),
    response_model=list[CommentResponse],
    responses={
        404: {"description": "Project not found"},
    },
)
async def list_comments(
    project_id: UUID,
    sort: Literal["top", "oldest", "newest"] = Query(
        default="top",
        description=(
            "Comment sort order: `top` by like count, `oldest` by creation time "
            "ascending, or `newest` by creation time descending."
        ),
    ),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> list[CommentResponse]:
    """Return comment payloads with placeholder handling, counts, and viewer state."""
    service = CommentService(db)
    try:
        return await service.list_comments(
            project_id=project_id,
            viewer_id=current_user.id if current_user else None,
            sort_by=sort,
        )
    except CommentProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc


@router.post(
    "/projects/{project_id}/comments",
    summary="Create project comment",
    description=(
        "Create a new flat comment on a published, non-deleted project. "
        "Authentication is required."
    ),
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Project not found"},
        422: {"description": "Validation error"},
    },
)
async def create_comment(
    project_id: UUID,
    payload: CommentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommentResponse:
    """Create a new comment and return the normalized response payload."""
    service = CommentService(db)
    try:
        return await service.create_comment(
            project_id=project_id,
            author_id=current_user.id,
            data=payload,
        )
    except CommentProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc


@router.post(
    "/comments/{comment_id}/like",
    summary="Like a comment",
    description=(
        "Like a comment as the authenticated user. This endpoint is idempotent: "
        "repeating the same request keeps the like present and still returns `204`."
    ),
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Comment not found"},
    },
)
async def like_comment(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Ensure the authenticated user has liked the target comment."""
    service = CommentLikeService(db)
    try:
        await service.add_like(comment_id=comment_id, user_id=current_user.id)
    except CommentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/comments/{comment_id}/like",
    summary="Unlike a comment",
    description=(
        "Remove the authenticated user's like from a comment. This endpoint is "
        "idempotent: repeating the same request leaves the comment unliked and "
        "still returns `204`."
    ),
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Comment not found"},
    },
)
async def unlike_comment(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Ensure the authenticated user no longer likes the target comment."""
    service = CommentLikeService(db)
    try:
        await service.remove_like(comment_id=comment_id, user_id=current_user.id)
    except CommentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/comments/{comment_id}",
    summary="Delete own comment",
    description=(
        "Soft-delete the authenticated author's own comment. Deleted comments remain "
        "in list results as placeholders."
    ),
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Comment delete forbidden"},
        404: {"description": "Comment not found"},
    },
)
async def delete_comment(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Soft-delete a comment owned by the current authenticated user."""
    service = CommentService(db)
    try:
        await service.delete_own_comment(
            comment_id=comment_id, actor_id=current_user.id
        )
    except CommentNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Comment not found") from exc
    except CommentForbiddenError as exc:
        raise HTTPException(status_code=403, detail="Comment delete forbidden") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/comments/{comment_id}/moderation",
    summary="Update comment moderation state",
    description=(
        "Admin-only moderation endpoint for hiding or restoring a comment without "
        "removing its row from the discussion list."
    ),
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Comment moderation forbidden"},
        404: {"description": "Comment not found"},
        422: {"description": "Validation error"},
    },
)
async def moderate_comment(
    comment_id: UUID,
    payload: CommentModerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Hide or restore a comment through the admin moderation policy."""
    require_policy(
        lambda: require_comment_moderation(current_user),
        detail="Comment moderation forbidden",
    )
    service = CommentService(db)
    try:
        await service.moderate_comment(
            comment_id=comment_id,
            moderation_state=payload.moderation_state,
        )
    except CommentNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Comment not found") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/comments/{comment_id}/moderation",
    summary="Moderator delete comment",
    description=(
        "Admin-only moderation endpoint that soft-deletes any comment. Deleted comments "
        "remain in list results as placeholders."
    ),
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Comment moderation forbidden"},
        404: {"description": "Comment not found"},
    },
)
async def moderator_delete_comment(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Soft-delete any comment through the admin moderation policy."""
    require_policy(
        lambda: require_comment_moderation(current_user),
        detail="Comment moderation forbidden",
    )
    service = CommentService(db)
    try:
        await service.moderator_delete_comment(comment_id=comment_id)
    except CommentNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Comment not found") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
