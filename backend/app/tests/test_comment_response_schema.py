from datetime import datetime, timezone
from uuid import uuid4
from app.models.comment import Comment
from app.schemas.comment import CommentResponse


def test_comment_response_masks_body_if_deleted():
    comment = Comment(
        id=uuid4(),
        project_id=uuid4(),
        author_id=uuid4(),
        body="Secret information",
        moderation_state="visible",
        deleted_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    response = CommentResponse.from_model(comment, like_count=0, viewer_has_liked=False)
    
    assert response.body == "[This comment has been removed or hidden by moderation]"
    assert response.author_id is None
    assert response.is_deleted is True


def test_comment_response_masks_body_if_hidden():
    comment = Comment(
        id=uuid4(),
        project_id=uuid4(),
        author_id=uuid4(),
        body="Secret information",
        moderation_state="hidden",
        deleted_at=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    response = CommentResponse.from_model(comment, like_count=0, viewer_has_liked=False)
    
    assert response.body == "[This comment has been removed or hidden by moderation]"
    assert response.author_id is None
    assert response.moderation_state == "hidden"
    assert response.is_deleted is False


def test_comment_response_shows_body_if_visible():
    comment = Comment(
        id=uuid4(),
        project_id=uuid4(),
        author_id=uuid4(),
        body="Great project!",
        moderation_state="visible",
        deleted_at=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    response = CommentResponse.from_model(comment, like_count=10, viewer_has_liked=True)
    
    assert response.body == "Great project!"
    assert response.author_id == comment.author_id
    assert response.like_count == 10
    assert response.viewer_has_liked is True
    assert response.is_deleted is False
