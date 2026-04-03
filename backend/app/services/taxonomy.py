from typing import TypeAlias

from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.taxonomy import Category, Tag, TechStack
from app.schemas.taxonomy import TaxonomyTermCreateRequest, TaxonomyTermResponse

TaxonomyModel: TypeAlias = Category | Tag | TechStack


class TaxonomyConflictError(ValueError):
    """Raised when a taxonomy term conflicts with an existing normalized value."""


def normalize_taxonomy_name(value: str) -> str:
    return value.strip().lower()


class TaxonomyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_categories(self) -> list[TaxonomyTermResponse]:
        return await self._list_terms(Category)

    async def list_tags(self) -> list[TaxonomyTermResponse]:
        return await self._list_terms(Tag)

    async def list_tech_stacks(self) -> list[TaxonomyTermResponse]:
        return await self._list_terms(TechStack)

    async def create_category(
        self, payload: TaxonomyTermCreateRequest
    ) -> TaxonomyTermResponse:
        return await self._create_term(Category, payload)

    async def create_tag(
        self, payload: TaxonomyTermCreateRequest
    ) -> TaxonomyTermResponse:
        return await self._create_term(Tag, payload)

    async def create_tech_stack(
        self, payload: TaxonomyTermCreateRequest
    ) -> TaxonomyTermResponse:
        return await self._create_term(TechStack, payload)

    async def _list_terms(
        self, model: type[TaxonomyModel]
    ) -> list[TaxonomyTermResponse]:
        model_cols = getattr(model, "__table__").c
        statement = select(model).order_by(
            model_cols.normalized_name.asc(),
            model_cols.id.asc(),
        )
        result = await self.db.exec(statement)
        return [TaxonomyTermResponse.model_validate(term) for term in result.all()]

    async def _create_term(
        self,
        model: type[TaxonomyModel],
        payload: TaxonomyTermCreateRequest,
    ) -> TaxonomyTermResponse:
        normalized_name = normalize_taxonomy_name(payload.name)
        model_cols = getattr(model, "__table__").c

        existing_statement = select(model).where(
            model_cols.normalized_name == normalized_name
        )
        existing_result = await self.db.exec(existing_statement)
        if existing_result.first() is not None:
            raise TaxonomyConflictError("Taxonomy term already exists")

        term = model(  # pyright: ignore[reportCallIssue]
            name=payload.name,
            normalized_name=normalized_name,
        )
        try:
            self.db.add(term)
            await self.db.commit()
            await self.db.refresh(term)
        except IntegrityError as exc:
            await self.db.rollback()
            raise TaxonomyConflictError("Taxonomy term already exists") from exc
        except Exception:
            await self.db.rollback()
            raise

        return TaxonomyTermResponse.model_validate(term)
