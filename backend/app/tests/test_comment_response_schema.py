from datetime import datetime, timezone
from uuid import uuid4

from app.models.comment import COMMENT_MODERATION_HIDDEN, Comment
from app.schemas.comment import (
    COMMENT_PLACEHOLDER_DELETED,
    COMMENT_PLACEHOLDER_HIDDEN,
    CommentResponse,
)


def _build_comment(
    *, moderation_state: str = "visible", deleted: bool = False
) -> Comment:
    now = datetime.now(timezone.utc)
    return Comment(
        id=uuid4(),
        project_id=uuid4(),
        author_id=uuid4(),
        body="Secret information",
        moderation_state=moderation_state,
        deleted_at=now if deleted else None,
        created_at=now,
        updated_at=now,
    )


def test_comment_response_masks_body_if_deleted():
    comment = _build_comment(deleted=True)

    response = CommentResponse.from_record(
        comment=comment,
        like_count=0,
        viewer_has_liked=False,
    )

    assert response.body == COMMENT_PLACEHOLDER_DELETED
    assert response.author.user_id is None
    assert response.is_deleted is True
    assert response.is_hidden is False


def test_comment_response_masks_body_if_hidden():
    comment = _build_comment(moderation_state=COMMENT_MODERATION_HIDDEN)

    response = CommentResponse.from_record(
        comment=comment,
        like_count=0,
        viewer_has_liked=False,
    )

    assert response.body == COMMENT_PLACEHOLDER_HIDDEN
    assert response.author.user_id is None
    assert response.is_hidden is True
    assert response.is_deleted is False


def test_comment_response_shows_body_if_visible():
    comment = _build_comment()

    response = CommentResponse.from_record(
        comment=comment,
        like_count=10,
        viewer_has_liked=True,
        username="commenter",
        full_name="Comment Person",
    )

    assert response.body == "Secret information"
    assert response.author.user_id == comment.author_id
    assert response.author.username == "commenter"
    assert response.like_count == 10
    assert response.viewer_has_liked is True
    assert response.is_deleted is False
