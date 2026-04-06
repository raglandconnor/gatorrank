from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps.auth import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthLoginRequest,
    AuthLogoutRequest,
    AuthMeResponse,
    AuthRefreshRequest,
    AuthSignupRequest,
    AuthTokenResponse,
    AuthUserResponse,
)
from app.services.auth import (
    AuthService,
    DuplicateEmailError,
    DuplicateUsernameError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)

router = APIRouter()


@router.post(
    "/auth/signup",
    summary="Sign up with email and password",
    description=(
        "Create a first-party user account and return an authenticated token payload. "
        "This endpoint enforces password policy, requires a canonical lowercase "
        "username, and supports optional `remember_me` refresh-session duration "
        "selection."
    ),
    response_model=AuthTokenResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"description": "Email or username already registered"},
        422: {"description": "Validation error"},
    },
)
async def signup(
    payload: AuthSignupRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthTokenResponse:
    """Create an account, then issue access + refresh tokens."""
    service = AuthService(db)
    try:
        user = await service.create_user(
            email=payload.email,
            username=payload.username,
            password=payload.password,
            full_name=payload.full_name,
        )
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except DuplicateUsernameError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    tokens = await service.issue_token_pair(user=user, remember_me=payload.remember_me)
    return AuthTokenResponse(
        access_token=tokens.access_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        refresh_token=tokens.refresh_token,
        refresh_token_expires_in=tokens.refresh_token_expires_in,
        user=AuthUserResponse.model_validate(user),
    )


@router.post(
    "/auth/login",
    summary="Log in with email and password",
    description=(
        "Validate first-party credentials and return an authenticated token payload. "
        "Invalid credentials return a generic error message."
    ),
    response_model=AuthTokenResponse,
    responses={
        401: {"description": "Invalid credentials"},
        422: {"description": "Validation error"},
    },
)
async def login(
    payload: AuthLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthTokenResponse:
    """Authenticate credentials and issue access + refresh tokens."""
    service = AuthService(db)
    try:
        user = await service.authenticate_user(
            email=payload.email,
            password=payload.password,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    tokens = await service.issue_token_pair(user=user, remember_me=payload.remember_me)
    return AuthTokenResponse(
        access_token=tokens.access_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        refresh_token=tokens.refresh_token,
        refresh_token_expires_in=tokens.refresh_token_expires_in,
        user=AuthUserResponse.model_validate(user),
    )


@router.get(
    "/auth/me",
    summary="Get authenticated user profile",
    description="Return the authenticated user's existing profile fields.",
    response_model=AuthMeResponse,
    responses={401: {"description": "Authentication required"}},
)
async def auth_me(current_user: User = Depends(get_current_user)) -> AuthMeResponse:
    """Return the current authenticated user profile."""
    return AuthMeResponse.model_validate(current_user)


@router.post(
    "/auth/refresh",
    summary="Rotate refresh token",
    description=(
        "Rotate an active refresh token and return a new access + refresh token payload. "
        "Invalid, expired, or revoked refresh tokens return `401`."
    ),
    response_model=AuthTokenResponse,
    responses={
        401: {"description": "Invalid refresh token"},
        422: {"description": "Validation error"},
    },
)
async def refresh_auth_token(
    payload: AuthRefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthTokenResponse:
    """Rotate refresh token and issue a replacement token pair."""
    service = AuthService(db)
    try:
        tokens, user = await service.refresh_token_pair(
            refresh_token=payload.refresh_token
        )
    except InvalidRefreshTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    return AuthTokenResponse(
        access_token=tokens.access_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        refresh_token=tokens.refresh_token,
        refresh_token_expires_in=tokens.refresh_token_expires_in,
        user=AuthUserResponse.model_validate(user),
    )


@router.post(
    "/auth/logout",
    summary="Log out refresh session",
    description=(
        "Revoke the provided refresh session token. This endpoint is idempotent and "
        "always returns `204`."
    ),
    status_code=status.HTTP_204_NO_CONTENT,
    responses={204: {"description": "Refresh session revoked (or already absent)"}},
)
async def logout(
    payload: AuthLogoutRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Revoke the provided refresh token session (idempotent)."""
    service = AuthService(db)
    await service.revoke_refresh_session(refresh_token=payload.refresh_token)
