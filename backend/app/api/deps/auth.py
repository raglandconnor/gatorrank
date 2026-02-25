from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.db.database import get_db
from app.models.user import User

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


async def _resolve_authenticated_user(
    request: Request,
    token: str,
    db: AsyncSession,
) -> User:
    """Validate a bearer token, sync request auth state, and return/upsert the user."""
    try:
        payload = jwt.decode(
            token,
            settings.DATABASE_JWT_SECRET,
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
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    # Shared Contract: Set auth context in backend request state
    request.state.current_user_id = user_id
    request.state.current_user_email = email

    # Upsert user on first authenticated request
    result = await db.exec(select(User).where(User.id == user_id))

    user = result.one_or_none()

    if not user:
        user = User(id=user_id, email=email)  # pyright: ignore[reportCallIssue]
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Require a valid bearer token and return the authenticated user."""
    return await _resolve_authenticated_user(request, credentials.credentials, db)


async def get_current_user_optional(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_security),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    # Missing auth is allowed here; malformed/expired tokens still fail.
    if credentials is None:
        if request.headers.get("Authorization"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
            )
        return None
    return await _resolve_authenticated_user(request, credentials.credentials, db)


def get_current_user_id_optional(request: Request) -> UUID | None:
    """Read optional auth context from request.state without performing token validation."""
    raw_user_id = getattr(request.state, "current_user_id", None)
    if raw_user_id is None:
        return None
    if isinstance(raw_user_id, UUID):
        return raw_user_id
    try:
        return UUID(str(raw_user_id))
    except ValueError:
        return None
