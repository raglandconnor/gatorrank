from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.models.project import Project
from app.models.taxonomy import (
    Category,
    ProjectCategory,
    ProjectTag,
    ProjectTechStack,
    Tag,
    TechStack,
)
from app.models.user import User


async def _seed_user(db_session, email: str) -> User:
    now = datetime.now(timezone.utc)
    user = User(
        email=email,
        username=f"user_{uuid4().hex[:10]}",
        password_hash="integration-password-hash",
        role="student",
        created_at=now,
        updated_at=now,
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def _seed_project(db_session, *, created_by_id) -> Project:
    now = datetime.now(timezone.utc)
    project = Project(
        created_by_id=created_by_id,
        title="Taxonomy Integration Project",
        short_description="Taxonomy integration test project",
        vote_count=0,
        is_group_project=False,
        is_published=False,
        published_at=None,
        created_at=now,
        updated_at=now,
    )
    db_session.add(project)
    await db_session.flush()
    return project


@pytest.mark.asyncio
async def test_taxonomy_normalized_name_unique_within_each_vocabulary(db_session):
    now = datetime.now(timezone.utc)
    category_one = Category(
        name="React",
        normalized_name="react",
        created_at=now,
    )
    db_session.add(category_one)
    await db_session.flush()

    category_duplicate = Category(
        name="REACT",
        normalized_name="react",
        created_at=now,
    )
    with pytest.raises(IntegrityError):
        async with db_session.begin_nested():
            db_session.add(category_duplicate)
            await db_session.flush()


@pytest.mark.asyncio
async def test_tag_normalized_name_unique_within_vocabulary(db_session):
    now = datetime.now(timezone.utc)
    tag_one = Tag(
        name="Backend",
        normalized_name="backend",
        created_at=now,
    )
    db_session.add(tag_one)
    await db_session.flush()

    tag_duplicate = Tag(
        name="BACKEND",
        normalized_name="backend",
        created_at=now,
    )
    with pytest.raises(IntegrityError):
        async with db_session.begin_nested():
            db_session.add(tag_duplicate)
            await db_session.flush()


@pytest.mark.asyncio
async def test_tech_stack_normalized_name_unique_within_vocabulary(db_session):
    now = datetime.now(timezone.utc)
    stack_one = TechStack(
        name="PostgreSQL",
        normalized_name="postgresql",
        created_at=now,
    )
    db_session.add(stack_one)
    await db_session.flush()

    stack_duplicate = TechStack(
        name="POSTGRESQL",
        normalized_name="postgresql",
        created_at=now,
    )
    with pytest.raises(IntegrityError):
        async with db_session.begin_nested():
            db_session.add(stack_duplicate)
            await db_session.flush()


@pytest.mark.asyncio
async def test_same_normalized_label_allowed_across_vocabularies(db_session):
    now = datetime.now(timezone.utc)
    category = Category(name="AI", normalized_name="ai", created_at=now)
    tag = Tag(name="AI", normalized_name="ai", created_at=now)
    tech_stack = TechStack(name="AI", normalized_name="ai", created_at=now)

    db_session.add(category)
    db_session.add(tag)
    db_session.add(tech_stack)
    await db_session.flush()

    assert category.id is not None
    assert tag.id is not None
    assert tech_stack.id is not None


@pytest.mark.asyncio
async def test_project_category_join_enforces_unique_pair(db_session):
    now = datetime.now(timezone.utc)
    user = await _seed_user(db_session, "taxonomy-pair-position@ufl.edu")
    project = await _seed_project(db_session, created_by_id=user.id)

    category_one = Category(name="Web", normalized_name="web", created_at=now)
    db_session.add(category_one)
    await db_session.flush()

    first_link = ProjectCategory(
        project_id=project.id,
        category_id=category_one.id,
        position=0,
        created_at=now,
    )
    db_session.add(first_link)
    await db_session.flush()

    duplicate_pair = ProjectCategory(
        project_id=project.id,
        category_id=category_one.id,
        position=1,
        created_at=now,
    )
    with pytest.raises(IntegrityError):
        async with db_session.begin_nested():
            db_session.add(duplicate_pair)
            await db_session.flush()


@pytest.mark.asyncio
async def test_project_category_join_enforces_unique_position(db_session):
    now = datetime.now(timezone.utc)
    user = await _seed_user(db_session, "taxonomy-position-only@ufl.edu")
    project = await _seed_project(db_session, created_by_id=user.id)

    category_one = Category(name="Web", normalized_name="web", created_at=now)
    category_two = Category(name="ML", normalized_name="ml", created_at=now)
    db_session.add(category_one)
    db_session.add(category_two)
    await db_session.flush()

    db_session.add(
        ProjectCategory(
            project_id=project.id,
            category_id=category_one.id,
            position=0,
            created_at=now,
        )
    )
    await db_session.flush()

    with pytest.raises(IntegrityError):
        async with db_session.begin_nested():
            db_session.add(
                ProjectCategory(
                    project_id=project.id,
                    category_id=category_two.id,
                    position=0,
                    created_at=now,
                )
            )
            await db_session.flush()


@pytest.mark.asyncio
async def test_project_tag_and_tech_stack_positions_represent_order(db_session):
    now = datetime.now(timezone.utc)
    user = await _seed_user(db_session, "taxonomy-order@ufl.edu")
    project = await _seed_project(db_session, created_by_id=user.id)

    tag_one = Tag(name="Backend", normalized_name="backend", created_at=now)
    tag_two = Tag(name="Frontend", normalized_name="frontend", created_at=now)
    stack_one = TechStack(name="FastAPI", normalized_name="fastapi", created_at=now)
    stack_two = TechStack(
        name="PostgreSQL",
        normalized_name="postgresql",
        created_at=now,
    )
    db_session.add(tag_one)
    db_session.add(tag_two)
    db_session.add(stack_one)
    db_session.add(stack_two)
    await db_session.flush()

    db_session.add(
        ProjectTag(project_id=project.id, tag_id=tag_one.id, position=0, created_at=now)
    )
    db_session.add(
        ProjectTag(project_id=project.id, tag_id=tag_two.id, position=1, created_at=now)
    )
    db_session.add(
        ProjectTechStack(
            project_id=project.id,
            tech_stack_id=stack_one.id,
            position=0,
            created_at=now,
        )
    )
    db_session.add(
        ProjectTechStack(
            project_id=project.id,
            tech_stack_id=stack_two.id,
            position=1,
            created_at=now,
        )
    )
    await db_session.flush()

    project_tag_cols = getattr(ProjectTag, "__table__").c
    project_tech_stack_cols = getattr(ProjectTechStack, "__table__").c
    tag_rows = (
        await db_session.exec(
            select(ProjectTag)
            .where(project_tag_cols.project_id == project.id)
            .order_by(project_tag_cols.position.asc())
        )
    ).all()
    stack_rows = (
        await db_session.exec(
            select(ProjectTechStack)
            .where(project_tech_stack_cols.project_id == project.id)
            .order_by(project_tech_stack_cols.position.asc())
        )
    ).all()

    assert [row.tag_id for row in tag_rows] == [tag_one.id, tag_two.id]
    assert [row.tech_stack_id for row in stack_rows] == [stack_one.id, stack_two.id]


@pytest.mark.asyncio
async def test_project_tag_join_enforces_unique_pair_and_position(db_session):
    now = datetime.now(timezone.utc)
    user = await _seed_user(db_session, "taxonomy-tag-constraints@ufl.edu")
    project = await _seed_project(db_session, created_by_id=user.id)

    tag_one = Tag(name="Backend", normalized_name="backend", created_at=now)
    tag_two = Tag(name="Frontend", normalized_name="frontend", created_at=now)
    db_session.add(tag_one)
    db_session.add(tag_two)
    await db_session.flush()

    db_session.add(
        ProjectTag(project_id=project.id, tag_id=tag_one.id, position=0, created_at=now)
    )
    await db_session.flush()

    with pytest.raises(IntegrityError):
        async with db_session.begin_nested():
            db_session.add(
                ProjectTag(
                    project_id=project.id,
                    tag_id=tag_one.id,
                    position=1,
                    created_at=now,
                )
            )
            await db_session.flush()

    with pytest.raises(IntegrityError):
        async with db_session.begin_nested():
            db_session.add(
                ProjectTag(
                    project_id=project.id,
                    tag_id=tag_two.id,
                    position=0,
                    created_at=now,
                )
            )
            await db_session.flush()


@pytest.mark.asyncio
async def test_project_tech_stack_join_enforces_unique_pair_and_position(db_session):
    now = datetime.now(timezone.utc)
    user = await _seed_user(db_session, "taxonomy-tech-stack-constraints@ufl.edu")
    project = await _seed_project(db_session, created_by_id=user.id)

    stack_one = TechStack(name="FastAPI", normalized_name="fastapi", created_at=now)
    stack_two = TechStack(
        name="PostgreSQL",
        normalized_name="postgresql",
        created_at=now,
    )
    db_session.add(stack_one)
    db_session.add(stack_two)
    await db_session.flush()

    db_session.add(
        ProjectTechStack(
            project_id=project.id,
            tech_stack_id=stack_one.id,
            position=0,
            created_at=now,
        )
    )
    await db_session.flush()

    with pytest.raises(IntegrityError):
        async with db_session.begin_nested():
            db_session.add(
                ProjectTechStack(
                    project_id=project.id,
                    tech_stack_id=stack_one.id,
                    position=1,
                    created_at=now,
                )
            )
            await db_session.flush()

    with pytest.raises(IntegrityError):
        async with db_session.begin_nested():
            db_session.add(
                ProjectTechStack(
                    project_id=project.id,
                    tech_stack_id=stack_two.id,
                    position=0,
                    created_at=now,
                )
            )
            await db_session.flush()


@pytest.mark.asyncio
async def test_join_tables_enforce_foreign_keys(db_session):
    now = datetime.now(timezone.utc)
    user = await _seed_user(db_session, "taxonomy-fk@ufl.edu")
    project = await _seed_project(db_session, created_by_id=user.id)
    category = Category(name="Web", normalized_name="web", created_at=now)
    tag = Tag(name="Backend", normalized_name="backend", created_at=now)
    stack = TechStack(name="FastAPI", normalized_name="fastapi", created_at=now)
    db_session.add(category)
    db_session.add(tag)
    db_session.add(stack)
    await db_session.flush()

    with pytest.raises(IntegrityError):
        async with db_session.begin_nested():
            db_session.add(
                ProjectCategory(
                    project_id=uuid4(),
                    category_id=category.id,
                    position=0,
                    created_at=now,
                )
            )
            await db_session.flush()

    with pytest.raises(IntegrityError):
        async with db_session.begin_nested():
            db_session.add(
                ProjectTag(
                    project_id=project.id,
                    tag_id=uuid4(),
                    position=0,
                    created_at=now,
                )
            )
            await db_session.flush()

    with pytest.raises(IntegrityError):
        async with db_session.begin_nested():
            db_session.add(
                ProjectTechStack(
                    project_id=uuid4(),
                    tech_stack_id=stack.id,
                    position=0,
                    created_at=now,
                )
            )
            await db_session.flush()


@pytest.mark.asyncio
async def test_created_at_uses_server_default_when_omitted(db_session):
    user = await _seed_user(db_session, "taxonomy-created-at-default@ufl.edu")
    project = await _seed_project(db_session, created_by_id=user.id)
    category = Category(  # pyright: ignore[reportCallIssue]
        name="Dev Tools",
        normalized_name="dev tools",
    )
    db_session.add(category)
    await db_session.flush()
    await db_session.refresh(category)

    assert category.created_at is not None

    project_category = ProjectCategory(  # pyright: ignore[reportCallIssue]
        project_id=project.id,
        category_id=category.id,
        position=0,
    )
    db_session.add(project_category)
    await db_session.flush()
    await db_session.refresh(project_category)

    assert project_category.created_at is not None
