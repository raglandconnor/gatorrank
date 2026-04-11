from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps.auth import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.services.comment_like import CommentLikeService, CommentNotFoundError

router = APIRouter()

@router.post(
    "/comments/{comment_id}/like",
    status_code=status.HTTP_200_OK,
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
    return {"message": "Like added"}


@router.delete(
    "/comments/{comment_id}/like",
    status_code=status.HTTP_200_OK,
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
    return {"message": "Like removed"}
