from uuid import uuid4

from app.models.comment import Comment


def test_comment_model_defaults():
    project_id = uuid4()
    author_id = uuid4()
    
    comment = Comment(
        project_id=project_id,
        author_id=author_id,
        body="This is a test comment.",
    )
    
    assert comment.project_id == project_id
    assert comment.author_id == author_id
    assert comment.body == "This is a test comment."
    
    # Defaults handled by model definition
    assert comment.moderation_state == "visible"
    assert comment.deleted_at is None
