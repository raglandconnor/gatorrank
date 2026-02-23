from uuid import UUID

from fastapi import Request


def get_current_user_id_optional(request: Request) -> UUID | None:
    # TODO: Replace request.state lookup with real Supabase JWT verification
    # and user extraction once auth middleware is implemented.
    """Return the current user id when auth middleware sets request.state."""
    raw_user_id = getattr(request.state, "current_user_id", None)
    if raw_user_id is None:
        return None
    if isinstance(raw_user_id, UUID):
        return raw_user_id
    try:
        return UUID(str(raw_user_id))
    except ValueError:
        return None
