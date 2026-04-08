from datetime import date, datetime, timezone
from typing import cast
from uuid import uuid4

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.project import Project
from app.schemas.search import ProjectSearchRequest
from app.services.project import CursorError
from app.services.search import PostgresSearchService
from app.utils.pagination import decode_cursor_payload, encode_cursor_payload


class DummySession:
    pass


def _make_project() -> Project:
    now = datetime.now(timezone.utc)
    return Project(
        id=uuid4(),
        created_by_id=uuid4(),
        title="Search Cursor Project",
        slug=f"search-{uuid4().hex[:8]}",
        short_description="Search cursor description",
        long_description=None,
        demo_url=None,
        github_url=None,
        video_url=None,
        vote_count=5,
        is_group_project=False,
        is_published=True,
        published_at=now,
        created_at=now,
        updated_at=now,
    )


def test_build_search_signature_is_order_insensitive_for_filter_lists():
    service = PostgresSearchService(cast(AsyncSession, DummySession()))
    top_range = (date(2026, 1, 1), date(2026, 1, 31))
    first = ProjectSearchRequest(
        q="Rank",
        categories=["Data", "AI"],
        tags=["Python", "FastAPI"],
        tech_stack=["Postgres", "Bun"],
        sort="top",
        published_from=top_range[0],
        published_to=top_range[1],
    )
    second = ProjectSearchRequest(
        q="rank",
        categories=["ai", "data"],
        tags=["fastapi", "python"],
        tech_stack=["bun", "postgres"],
        sort="top",
        published_from=top_range[0],
        published_to=top_range[1],
    )

    first_sig = service._build_search_signature(request=first, top_range=top_range)
    second_sig = service._build_search_signature(request=second, top_range=top_range)

    assert first_sig == second_sig


def test_decode_cursor_rejects_search_signature_mismatch():
    service = PostgresSearchService(cast(AsyncSession, DummySession()))
    project = _make_project()
    top_range = (project.created_at.date(), project.created_at.date())
    cursor = service._encode_cursor(
        project=project,
        sort="top",
        search_signature="sig-a",
        top_range=top_range,
    )

    with pytest.raises(CursorError, match="Cursor does not match requested search"):
        service._decode_cursor(
            cursor=cursor,
            sort="top",
            search_signature="sig-b",
            top_range=top_range,
        )


def test_decode_cursor_rejects_sort_mismatch():
    service = PostgresSearchService(cast(AsyncSession, DummySession()))
    project = _make_project()
    cursor = service._encode_cursor(
        project=project,
        sort="new",
        search_signature="sig-a",
        top_range=None,
    )

    with pytest.raises(CursorError, match="Invalid cursor"):
        service._decode_cursor(
            cursor=cursor,
            sort="top",
            search_signature="sig-a",
            top_range=(project.created_at.date(), project.created_at.date()),
        )


def test_resolve_top_date_range_rejects_invalid_range():
    with pytest.raises(CursorError, match="Invalid date range"):
        PostgresSearchService._resolve_top_date_range(
            sort="top",
            published_from=date(2026, 2, 1),
            published_to=date(2026, 1, 1),
        )


@pytest.mark.parametrize(
    ("mutate_payload", "expected_error"),
    [
        (
            lambda payload: {**payload, "search_sig": "tampered"},
            "Cursor does not match requested search",
        ),
        (
            lambda payload: {
                key: value for key, value in payload.items() if key != "created_at"
            },
            "Invalid cursor",
        ),
        (
            lambda payload: {**payload, "unexpected": "value"},
            "Invalid cursor",
        ),
        (
            lambda payload: {**payload, "id": "not-a-uuid"},
            "Invalid cursor",
        ),
        (
            lambda payload: {**payload, "created_at": "not-a-datetime"},
            "Invalid cursor",
        ),
    ],
)
def test_decode_cursor_rejects_tampered_or_malformed_payloads(
    mutate_payload, expected_error
):
    service = PostgresSearchService(cast(AsyncSession, DummySession()))
    project = _make_project()
    top_range = (project.created_at.date(), project.created_at.date())
    cursor = service._encode_cursor(
        project=project,
        sort="top",
        search_signature="sig-a",
        top_range=top_range,
    )
    payload = decode_cursor_payload(cursor)
    mutated_payload = mutate_payload(payload)
    tampered_cursor = encode_cursor_payload(mutated_payload)

    with pytest.raises(CursorError, match=expected_error):
        service._decode_cursor(
            cursor=tampered_cursor,
            sort="top",
            search_signature="sig-a",
            top_range=top_range,
        )
