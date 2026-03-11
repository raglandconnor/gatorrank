from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import secrets

import jwt
import sqlalchemy as sa
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import update
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


class DuplicateEmailError(ValueError):
    """Raised when attempting to create an already-registered email."""


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
    def normalize_full_name(full_name: str | None) -> str | None:
        if full_name is None:
            return None
        normalized = full_name.strip()
        return normalized or None

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

    @staticmethod
    def validate_password_policy(password: str) -> None:
        if password.strip() == "":
            raise InvalidCredentialsError("Password cannot be whitespace only")
        if len(password) < 12:
            raise InvalidCredentialsError("Password must be at least 12 characters")
        if len(password) > 128:
            raise InvalidCredentialsError("Password must be at most 128 characters")

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

    async def create_user(
        self,
        *,
        email: str,
        password: str,
        full_name: str | None = None,
    ) -> User:
        self.validate_password_policy(password)
        normalized_email = self.normalize_email(email)
        normalized_full_name = self.normalize_full_name(full_name)

        existing = await self.get_user_by_email(normalized_email)
        if existing is not None:
            raise DuplicateEmailError("Email already registered")

        user = User(  # pyright: ignore[reportCallIssue]
            email=normalized_email,
            password_hash=self.hash_password(password),
            full_name=normalized_full_name,
            role="student",
        )
        try:
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
        except IntegrityError as exc:
            await self.db.rollback()
            raise DuplicateEmailError("Email already registered") from exc
        except Exception:
            await self.db.rollback()
            raise

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

    async def refresh_token_pair(self, *, refresh_token: str) -> tuple[TokenPair, User]:
        try:
            now = datetime.now(UTC)
            refresh_token_hash = self.hash_refresh_token(refresh_token)
            refresh_session_cols = getattr(RefreshSession, "__table__").c

            # Atomically claim (revoke) the active refresh session to prevent replay races.
            revoke_statement = (
                update(RefreshSession)
                .where(
                    refresh_session_cols.token_hash == refresh_token_hash,
                    refresh_session_cols.revoked_at.is_(None),
                )
                .values(revoked_at=now)
                .returning(
                    refresh_session_cols.id,
                    refresh_session_cols.user_id,
                    refresh_session_cols.created_at,
                    refresh_session_cols.expires_at,
                )
            )
            revoked_row_result = await self.db.exec(revoke_statement)
            revoked_row = revoked_row_result.one_or_none()
            if revoked_row is None:
                raise InvalidRefreshTokenError("Invalid refresh token")

            session_user_id = revoked_row[1]
            session_created_at = revoked_row[2]
            session_expires_at = revoked_row[3]
            if session_expires_at <= now:
                await self.db.commit()
                raise InvalidRefreshTokenError("Invalid refresh token")

            user_result = await self.db.exec(
                select(User).where(User.id == session_user_id)
            )
            user = user_result.first()
            if user is None:
                await self.db.commit()
                raise InvalidRefreshTokenError("Invalid refresh token")

            original_ttl = self._derive_original_refresh_ttl(
                RefreshSession(  # pyright: ignore[reportCallIssue]
                    id=revoked_row[0],
                    user_id=session_user_id,
                    token_hash=refresh_token_hash,
                    created_at=session_created_at,
                    expires_at=session_expires_at,
                    revoked_at=now,
                )
            )
            next_refresh_token = secrets.token_urlsafe(REFRESH_TOKEN_BYTES)
            next_refresh_token_hash = self.hash_refresh_token(next_refresh_token)
            replacement_session = RefreshSession(  # pyright: ignore[reportCallIssue]
                user_id=user.id,
                token_hash=next_refresh_token_hash,
                expires_at=now + original_ttl,
                revoked_at=None,
            )
            self.db.add(replacement_session)
            await self.db.commit()

            return (
                self._build_token_pair(
                    user=user,
                    refresh_token=next_refresh_token,
                    refresh_ttl=original_ttl,
                    now=now,
                ),
                user,
            )
        except InvalidRefreshTokenError:
            raise
        except Exception:
            await self.db.rollback()
            raise

    async def revoke_refresh_session(self, *, refresh_token: str) -> bool:
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
            return False

        refresh_session.revoked_at = now
        self.db.add(refresh_session)
        await self.db.commit()
        return True
