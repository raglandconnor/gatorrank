from uuid import uuid4

from app.models.comment import (
    COMMENT_MODERATION_VISIBLE,
    Comment,
)


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
    assert comment.parent_comment_id is None
    assert comment.moderation_state == COMMENT_MODERATION_VISIBLE
    assert comment.deleted_at is None


def test_comment_schema_constraints_and_indexes():
    table = getattr(Comment, "__table__")

    assert table.c.project_id.nullable is False
    assert table.c.author_id.nullable is False
    assert table.c.parent_comment_id.nullable is True
    assert table.c.body.nullable is False
    assert table.c.moderation_state.nullable is False
    assert table.c.moderation_state.type.length == 32
    assert table.c.deleted_at.nullable is True

    index_names = {index.name for index in table.indexes}
    assert "ix_comments_project_id" in index_names
    assert "ix_comments_author_id" in index_names
    assert "ix_comments_project_id_created_at" in index_names
