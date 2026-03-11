from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings
from app.db.database import get_db
from app.models.user import User

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)
settings = get_settings()


async def _resolve_authenticated_user(
    request: Request,
    token: str,
    db: AsyncSession,
) -> User:
    """Validate a bearer token, sync request auth state, and return the user."""
    try:
        payload = jwt.decode(
            token,
            settings.DATABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        user_id_str = payload.get("sub")
        raw_email = payload.get("email")

        if not user_id_str or not isinstance(raw_email, str) or not raw_email.strip():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
            )

        user_id = UUID(user_id_str)
        email = raw_email.strip().lower()

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

    result = await db.exec(select(User).where(User.id == user_id))
    user = result.one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

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
