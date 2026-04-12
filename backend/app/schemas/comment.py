from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.comment import COMMENT_MODERATION_HIDDEN, CommentModerationState

COMMENT_PLACEHOLDER_DELETED = "[This comment was deleted by its author.]"
COMMENT_PLACEHOLDER_HIDDEN = "[This comment was hidden by a moderator.]"


class CommentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    body: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Comment body text. Leading and trailing whitespace is trimmed.",
    )

    @field_validator("body", mode="before")
    @classmethod
    def _trim_body(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class CommentAuthorResponse(BaseModel):
    user_id: UUID | None = None
    username: str | None = None
    full_name: str | None = None
    profile_picture_url: str | None = None


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    author: CommentAuthorResponse
    body: str
    moderation_state: CommentModerationState
    is_deleted: bool
    is_hidden: bool
    like_count: int = 0
    viewer_has_liked: bool = False
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_record(
        cls,
        *,
        comment,
        like_count: int,
        viewer_has_liked: bool,
        username: str | None = None,
        full_name: str | None = None,
        profile_picture_url: str | None = None,
    ) -> "CommentResponse":
        is_deleted = comment.deleted_at is not None
        is_hidden = comment.moderation_state == COMMENT_MODERATION_HIDDEN

        if is_deleted:
            body = COMMENT_PLACEHOLDER_DELETED
            author = CommentAuthorResponse()
        elif is_hidden:
            body = COMMENT_PLACEHOLDER_HIDDEN
            author = CommentAuthorResponse()
        else:
            body = comment.body
            author = CommentAuthorResponse(
                user_id=comment.author_id,
                username=username,
                full_name=full_name,
                profile_picture_url=profile_picture_url,
            )

        return cls(
            id=comment.id,
            project_id=comment.project_id,
            author=author,
            body=body,
            moderation_state=comment.moderation_state,
            is_deleted=is_deleted,
            is_hidden=is_hidden,
            like_count=like_count,
            viewer_has_liked=viewer_has_liked,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )


class CommentModerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    moderation_state: CommentModerationState = Field(
        ...,
        description=(
            "Comment moderation state. `visible` restores normal rendering and "
            "`hidden` returns a moderator placeholder in comment lists."
        ),
    )
