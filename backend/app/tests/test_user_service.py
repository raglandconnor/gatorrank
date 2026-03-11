from datetime import datetime, timezone
from typing import cast
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.user import User
from app.schemas.user import UserUpdate
from app.services.user import UserService


class DummySession:
    def __init__(self):
        self.add = Mock()
        self.commit = AsyncMock()
        self.refresh = AsyncMock()


def _build_user() -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=uuid4(),
        email="service-test@ufl.edu",
        password_hash="service-test-password-hash",
        full_name="Existing Name",
        profile_picture_url="https://example.com/old.jpg",
        role="student",
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_update_user_partial_profile_picture_only_updates_target_field():
    db = DummySession()
    service = UserService(cast(AsyncSession, db))
    user = _build_user()
    service.get_user_by_id = AsyncMock(return_value=user)  # type: ignore[method-assign]

    payload = UserUpdate.model_validate(
        {"profile_picture_url": "https://example.com/new.jpg"}
    )
    updated = await service.update_user(user.id, payload)

    assert updated is user
    assert user.full_name == "Existing Name"
    assert user.profile_picture_url == "https://example.com/new.jpg"
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(user)


@pytest.mark.asyncio
async def test_update_user_partial_full_name_updates_name():
    db = DummySession()
    service = UserService(cast(AsyncSession, db))
    user = _build_user()
    service.get_user_by_id = AsyncMock(return_value=user)  # type: ignore[method-assign]

    payload = UserUpdate(full_name="Updated Name")
    updated = await service.update_user(user.id, payload)

    assert updated is user
    assert user.full_name == "Updated Name"
    assert user.profile_picture_url == "https://example.com/old.jpg"
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(user)


@pytest.mark.asyncio
async def test_update_user_returns_none_when_user_is_missing():
    db = DummySession()
    service = UserService(cast(AsyncSession, db))
    service.get_user_by_id = AsyncMock(return_value=None)  # type: ignore[method-assign]

    payload = UserUpdate(full_name="New Name")
    updated = await service.update_user(uuid4(), payload)

    assert updated is None
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()
