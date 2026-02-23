from uuid import UUID

import jwt
import sqlalchemy as sa
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_db
from app.models.user import User

security = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        user_id_str = payload.get("sub")
        email = payload.get("email")

        if not user_id_str or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
            )

        user_id = UUID(user_id_str)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    # Shared Contract: Set auth context in backend request state
    request.state.current_user_id = user_id
    request.state.current_user_email = email

    # Ticket B2: Upsert user on first authenticated request
    result = await db.execute(sa.select(User).where(User.id == user_id))  # pyright: ignore[reportArgumentType]

    user = result.scalar_one_or_none()

    if not user:
        user = User(id=user_id, email=email)  # pyright: ignore[reportCallIssue]
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


def get_current_user_id_optional(request: Request) -> UUID | None:
    """Return the current user id when auth middleware sets request.state."""
    raw_user_id = getattr(request.state, "current_user_id", None)
    if raw_user_id is None:
        return None
    if isinstance(raw_user_id, UUID):
        return raw_user_id
    try:
        return UUID(str(raw_user_id))
    except ValueError:
        return None
