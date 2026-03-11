from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import secrets

import jwt
import sqlalchemy as sa
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings
from app.models.auth import RefreshSession
from app.models.user import User

ACCESS_TOKEN_TTL = timedelta(minutes=30)
REFRESH_TOKEN_TTL_DEFAULT = timedelta(days=14)
REFRESH_TOKEN_TTL_REMEMBER_ME = timedelta(days=180)
TOKEN_AUDIENCE = "authenticated"
TOKEN_TYPE = "bearer"
REFRESH_TOKEN_BYTES = 48


class InvalidCredentialsError(ValueError):
    """Raised when user credentials are invalid."""


class InvalidRefreshTokenError(ValueError):
    """Raised when refresh token validation fails."""


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    refresh_token_expires_in: int


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.password_hasher = PasswordHasher()

    @staticmethod
    def normalize_email(email: str) -> str:
        return email.strip().lower()

    @staticmethod
    def _refresh_ttl(remember_me: bool) -> timedelta:
        if remember_me:
            return REFRESH_TOKEN_TTL_REMEMBER_ME
        return REFRESH_TOKEN_TTL_DEFAULT

    def _issue_access_token(self, user: User, *, now: datetime) -> tuple[str, int]:
        exp = now + ACCESS_TOKEN_TTL
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "aud": TOKEN_AUDIENCE,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        token = jwt.encode(
            payload,
            self.settings.DATABASE_JWT_SECRET,
            algorithm="HS256",
        )
        return token, int(ACCESS_TOKEN_TTL.total_seconds())

    def hash_password(self, password: str) -> str:
        return self.password_hasher.hash(password)

    def verify_password(self, password: str, password_hash: str) -> bool:
        try:
            return self.password_hasher.verify(password_hash, password)
        except (VerifyMismatchError, InvalidHashError):
            return False

    async def get_user_by_email(self, email: str) -> User | None:
        normalized_email = self.normalize_email(email)
        statement = select(User).where(sa.func.lower(User.email) == normalized_email)
        result = await self.db.exec(statement)
        return result.first()

    async def authenticate_user(self, *, email: str, password: str) -> User:
        user = await self.get_user_by_email(email)
        if user is None:
            raise InvalidCredentialsError("Invalid credentials")
        if not self.verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid credentials")
        return user

    def hash_refresh_token(self, refresh_token: str) -> str:
        digest = hmac.new(
            self.settings.DATABASE_JWT_SECRET.encode("utf-8"),
            refresh_token.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return digest

    def _build_token_pair(
        self,
        *,
        user: User,
        refresh_token: str,
        refresh_ttl: timedelta,
        now: datetime,
    ) -> TokenPair:
        access_token, access_token_ttl_seconds = self._issue_access_token(user, now=now)
        return TokenPair(
            access_token=access_token,
            token_type=TOKEN_TYPE,
            expires_in=access_token_ttl_seconds,
            refresh_token=refresh_token,
            refresh_token_expires_in=int(refresh_ttl.total_seconds()),
        )

    async def issue_token_pair(self, *, user: User, remember_me: bool) -> TokenPair:
        now = datetime.now(UTC)
        refresh_ttl = self._refresh_ttl(remember_me)
        refresh_token = secrets.token_urlsafe(REFRESH_TOKEN_BYTES)
        refresh_token_hash = self.hash_refresh_token(refresh_token)
        refresh_session = RefreshSession(  # pyright: ignore[reportCallIssue]
            user_id=user.id,
            token_hash=refresh_token_hash,
            expires_at=now + refresh_ttl,
            revoked_at=None,
        )
        self.db.add(refresh_session)
        await self.db.commit()

        return self._build_token_pair(
            user=user,
            refresh_token=refresh_token,
            refresh_ttl=refresh_ttl,
            now=now,
        )

    @staticmethod
    def _derive_original_refresh_ttl(session: RefreshSession) -> timedelta:
        delta = session.expires_at - session.created_at
        if delta <= timedelta(seconds=0):
            return REFRESH_TOKEN_TTL_DEFAULT
        return delta

    async def refresh_token_pair(self, *, refresh_token: str) -> TokenPair:
        now = datetime.now(UTC)
        refresh_token_hash = self.hash_refresh_token(refresh_token)
        refresh_session_cols = getattr(RefreshSession, "__table__").c

        session_statement = select(RefreshSession).where(
            refresh_session_cols.token_hash == refresh_token_hash,
            refresh_session_cols.revoked_at.is_(None),
        )
        session_result = await self.db.exec(session_statement)
        refresh_session = session_result.first()
        if refresh_session is None:
            raise InvalidRefreshTokenError("Invalid refresh token")
        if refresh_session.expires_at <= now:
            raise InvalidRefreshTokenError("Invalid refresh token")

        user_result = await self.db.exec(
            select(User).where(User.id == refresh_session.user_id)
        )
        user = user_result.first()
        if user is None:
            raise InvalidRefreshTokenError("Invalid refresh token")

        original_ttl = self._derive_original_refresh_ttl(refresh_session)
        next_refresh_token = secrets.token_urlsafe(REFRESH_TOKEN_BYTES)
        next_refresh_token_hash = self.hash_refresh_token(next_refresh_token)

        refresh_session.revoked_at = now
        replacement_session = RefreshSession(  # pyright: ignore[reportCallIssue]
            user_id=user.id,
            token_hash=next_refresh_token_hash,
            expires_at=now + original_ttl,
            revoked_at=None,
        )
        self.db.add(refresh_session)
        self.db.add(replacement_session)
        await self.db.commit()

        return self._build_token_pair(
            user=user,
            refresh_token=next_refresh_token,
            refresh_ttl=original_ttl,
            now=now,
        )
