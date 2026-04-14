from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings
from app.db.database import get_db
from app.models.user import User
from app.services.auth_bootstrap import (
    AuthBootstrapService,
    AuthIdentity,
    EmailPolicyError,
    UsernameConflictError,
)

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)
settings = get_settings()
_jwk_client = jwt.PyJWKClient(settings.SUPABASE_JWKS_URL)


def _decode_supabase_jwt(token: str) -> dict[str, object]:
    signing_key = _jwk_client.get_signing_key_from_jwt(token).key
    payload = jwt.decode(
        token,
        signing_key,
        algorithms=["RS256", "ES256"],
        audience="authenticated",
        issuer=settings.SUPABASE_ISSUER,
        options={"require": ["sub", "email", "aud", "exp", "iat", "iss"]},
    )
    if not isinstance(payload, dict):
        raise ValueError("Invalid token payload")
    return payload


def _read_optional_str(payload: dict[str, object], key: str) -> str | None:
    raw = payload.get(key)
    if not isinstance(raw, str):
        return None
    normalized = raw.strip()
    return normalized or None


def _read_user_metadata(payload: dict[str, object]) -> dict[str, object]:
    metadata = payload.get("user_metadata")
    if isinstance(metadata, dict):
        return metadata
    return {}


def _read_email_confirmed(payload: dict[str, object]) -> bool | None:
    candidates = ("email_confirmed_at", "confirmed_at")
    for key in candidates:
        value = payload.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            return bool(value.strip())
        return bool(value)
    return None


async def _resolve_authenticated_user(
    request: Request,
    token: str,
    db: AsyncSession,
) -> User:
    """Validate a bearer token, sync request auth state, and return the user."""
    try:
        payload = _decode_supabase_jwt(token)
        auth_user_id_str = payload.get("sub")
        raw_email = payload.get("email")

        if (
            not auth_user_id_str
            or not isinstance(raw_email, str)
            or not raw_email.strip()
        ):
            raise ValueError("Invalid token payload")

        auth_user_id = UUID(str(auth_user_id_str))
        email = raw_email.strip().lower()
        metadata = _read_user_metadata(payload)
        username = _read_optional_str(metadata, "username")
        full_name = _read_optional_str(metadata, "full_name")
        email_confirmed = _read_email_confirmed(payload)

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
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    service = AuthBootstrapService(db, settings)
    try:
        user = await service.get_or_create_user(
            AuthIdentity(
                auth_user_id=auth_user_id,
                email=email,
                username=username,
                full_name=full_name,
                email_confirmed=email_confirmed,
            )
        )
    except EmailPolicyError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except UsernameConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc

    # Shared Contract: Set auth context in backend request state
    request.state.current_user_id = user.id
    request.state.current_user_email = user.email
    request.state.current_auth_user_id = auth_user_id
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
