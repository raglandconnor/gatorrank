import pytest
from pydantic import ValidationError

from app.schemas.auth import AuthMeResponse


def test_auth_me_response_rejects_unknown_role():
    with pytest.raises(ValidationError):
        AuthMeResponse.model_validate(
            {
                "id": "de42ce14-ee3f-40e5-a9e0-a513c54e17ef",
                "email": "user@ufl.edu",
                "role": "super_admin",
                "full_name": None,
                "profile_picture_url": None,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            }
        )
