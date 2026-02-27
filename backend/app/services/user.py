from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.user import User
from app.schemas.user import UserUpdate


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        statement = select(User).where(User.id == user_id)
        result = await self.db.exec(statement)
        return result.first()

    async def update_user(self, user_id: UUID, payload: UserUpdate) -> User | None:
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        # The schema validation guarantees full_name is present and non-empty
        user.full_name = payload.full_name
        user.profile_picture_url = payload.profile_picture_url

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
