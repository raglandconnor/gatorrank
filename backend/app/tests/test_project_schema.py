import pytest
from pydantic import ValidationError

from app.schemas.project import ProjectCreateRequest, ProjectUpdateRequest


def _base_create_payload(**overrides):
    payload = {
        "title": "Schema Test Project",
        "short_description": "Schema test project description",
        "github_url": "https://github.com/example/schema",
        "categories": [],
        "tags": [],
        "tech_stack": [],
    }
    payload.update(overrides)
    return payload


def test_project_create_accepts_taxonomy_term_length_boundaries():
    request = ProjectCreateRequest(
        **_base_create_payload(
            categories=["ab", "x" * 64],
            tags=["ab"],
            tech_stack=["ab"],
        )
    )
    assert request.categories == ["ab", "x" * 64]


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("categories", ["a"]),
        ("categories", ["x" * 65]),
        ("tags", ["a"]),
        ("tags", ["x" * 65]),
        ("tech_stack", ["a"]),
        ("tech_stack", ["x" * 65]),
    ],
)
def test_project_create_rejects_invalid_taxonomy_term_lengths(
    field_name: str, value: list[str]
):
    payload = _base_create_payload()
    payload[field_name] = value
    with pytest.raises(ValidationError):
        ProjectCreateRequest(**payload)


def test_project_create_rejects_duplicate_taxonomy_terms_after_normalization():
    with pytest.raises(ValidationError, match="Duplicate taxonomy terms"):
        ProjectCreateRequest(
            **_base_create_payload(categories=["AI", " ai "]),
        )


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("categories", ["Re\nact"]),
        ("categories", ["Re\u0085act"]),
        ("tags", ["AP\tI"]),
        ("tech_stack", ["Fast\u0085API"]),
    ],
)
def test_project_create_rejects_control_chars_in_taxonomy_terms(
    field_name: str, value: list[str]
):
    payload = _base_create_payload()
    payload[field_name] = value
    with pytest.raises(ValidationError, match="control characters"):
        ProjectCreateRequest(**payload)


@pytest.mark.parametrize("field_name", ["categories", "tags", "tech_stack"])
def test_project_update_rejects_null_taxonomy_field(field_name: str):
    with pytest.raises(ValidationError, match=f"{field_name} cannot be null"):
        ProjectUpdateRequest(**{field_name: None})
