from app.models.auth import RefreshSession
from app.models.user import User


def test_user_password_hash_column_is_required():
    table = getattr(User, "__table__")
    column = table.c.password_hash

    assert column.nullable is False
    assert column.type.length == 255


def test_refresh_session_schema_constraints_and_indexes():
    table = getattr(RefreshSession, "__table__")

    user_id_col = table.c.user_id
    token_hash_col = table.c.token_hash
    expires_at_col = table.c.expires_at
    revoked_at_col = table.c.revoked_at

    assert user_id_col.nullable is False
    assert token_hash_col.nullable is False
    assert token_hash_col.type.length == 128
    assert expires_at_col.nullable is False
    assert revoked_at_col.nullable is True

    unique_names = {
        constraint.name
        for constraint in table.constraints
        if constraint.name is not None
    }
    assert "uq_refresh_sessions_token_hash" in unique_names

    index_names = {index.name for index in table.indexes}
    assert "ix_refresh_sessions_user_id" in index_names
    assert "ix_refresh_sessions_token_hash" in index_names
    assert "ix_refresh_sessions_expires_at" in index_names
