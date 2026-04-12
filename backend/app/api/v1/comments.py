from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps.auth import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.services.comment_like import CommentLikeService, CommentNotFoundError

router = APIRouter()


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
