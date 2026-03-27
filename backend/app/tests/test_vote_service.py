from typing import cast
from uuid import uuid4

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.services.vote import VoteService
from app.utils.pagination import encode_cursor_payload
from app.utils.pagination import CursorError


class DummySession:
    pass


def test_decode_recent_votes_cursor_rejects_malformed_cursor():
    service = VoteService(cast(AsyncSession, DummySession()))

    with pytest.raises(CursorError, match="Invalid cursor"):
        service._decode_recent_votes_cursor("not-a-valid-cursor")


def test_decode_recent_votes_cursor_rejects_sort_mismatch():
    service = VoteService(cast(AsyncSession, DummySession()))
    cursor = encode_cursor_payload(
        {
            "sort": "new",
            "voted_at": "2026-03-25T12:30:00+00:00",
            "project_id": str(uuid4()),
        }
    )

    with pytest.raises(CursorError, match="Invalid cursor"):
        service._decode_recent_votes_cursor(cursor)
