import pytest
from pydantic import ValidationError

from app.schemas.search import ProjectSearchRequest


def test_project_search_request_defaults():
    payload = ProjectSearchRequest()

    assert payload.q is None
    assert payload.categories == []
    assert payload.tags == []
    assert payload.tech_stack == []
    assert payload.sort == "top"
    assert payload.limit == 20
    assert payload.cursor is None


def test_project_search_request_normalizes_query_and_cursor():
    payload = ProjectSearchRequest(q="  gator rank ", cursor="  abc123  ")

    assert payload.q == "gator rank"
    assert payload.cursor == "abc123"


def test_project_search_request_treats_whitespace_query_as_omitted():
    payload = ProjectSearchRequest(q="   ")
    assert payload.q is None


def test_project_search_request_normalizes_and_deduplicates_taxonomy_terms():
    payload = ProjectSearchRequest(
        categories=["  AI  ", "ai", "", " Robotics "],
        tags=["python", "Python", " "],
        tech_stack=["FastAPI", "fastapi"],
    )

    assert payload.categories == ["AI", "Robotics"]
    assert payload.tags == ["python"]
    assert payload.tech_stack == ["FastAPI"]


def test_project_search_request_rejects_control_chars_in_filter_terms():
    with pytest.raises(ValidationError, match="control characters"):
        ProjectSearchRequest(tags=["bad\x01term"])
