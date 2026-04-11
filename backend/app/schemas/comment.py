from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CommentCreateRequest(BaseModel):
    body: str = Field(..., max_length=5000, description="The body text of the comment")


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    author_id: UUID | None = None
    body: str | None = None
    moderation_state: str = "visible"
    like_count: int = 0
    viewer_has_liked: bool = False
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_model(cls, comment, like_count: int, viewer_has_liked: bool):
        is_deleted = comment.deleted_at is not None
        is_hidden = comment.moderation_state != "visible" or is_deleted

        body = comment.body
        author_id = comment.author_id

        if is_hidden:
            body = "[This comment has been removed or hidden by moderation]"
            author_id = None
        
        return cls(
            id=comment.id,
            project_id=comment.project_id,
            author_id=author_id,
            body=body,
            moderation_state=comment.moderation_state,
            like_count=like_count,
            viewer_has_liked=viewer_has_liked,
            is_deleted=is_deleted,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )
