from unittest.mock import AsyncMock

import pytest

from app.schemas.taxonomy import TaxonomyTermCreateRequest
from app.services.taxonomy import (
    TaxonomyConflictError,
    TaxonomyService,
    normalize_taxonomy_name,
)


class _ResultWithFirst:
    def __init__(self, value):
        self._value = value

    def first(self):
        return self._value


def test_normalize_taxonomy_name_trims_and_lowercases():
    assert normalize_taxonomy_name("  React Native  ") == "react native"


@pytest.mark.asyncio
async def test_create_category_raises_conflict_when_normalized_name_exists():
    db = AsyncMock()
    db.exec = AsyncMock(return_value=_ResultWithFirst(object()))
    service = TaxonomyService(db)
    payload = TaxonomyTermCreateRequest(name="  React  ")

    with pytest.raises(TaxonomyConflictError, match="already exists"):
        await service.create_category(payload)

    db.add.assert_not_called()
    db.commit.assert_not_called()
