import pytest
from pydantic import ValidationError

from app.schemas.user import UserPrivate


def test_auth_me_response_rejects_unknown_role():
    with pytest.raises(ValidationError):
        UserPrivate.model_validate(
            {
                "id": "de42ce14-ee3f-40e5-a9e0-a513c54e17ef",
                "email": "user@ufl.edu",
                "username": "user_name",
                "role": "super_admin",
                "full_name": None,
                "profile_picture_url": None,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            }
        )
