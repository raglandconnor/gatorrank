from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import Settings
from app.models.user import User
from app.models.user_roles import USER_ROLE_STUDENT
from app.utils.username import validate_username


class AuthBootstrapError(ValueError):
    """Raised when an authenticated identity cannot be mapped to an app user."""


class UsernameConflictError(AuthBootstrapError):
    """Raised when a username collision blocks first-user bootstrap."""


class EmailPolicyError(AuthBootstrapError):
    """Raised when identity does not satisfy required email policies."""


@dataclass(frozen=True)
class AuthIdentity:
    auth_user_id: UUID
    email: str
    username: str | None
    full_name: str | None
    email_confirmed: bool | None


class SupabaseAdminClient:
    """Minimal server-side Supabase Auth admin client used for bootstrap validation."""

    def __init__(self, settings: Settings):
        self._base = settings.SUPABASE_URL.rstrip("/")
        self._secret = settings.SUPABASE_SECRET_KEY

    def get_user(self, auth_user_id: UUID) -> dict[str, Any]:
        url = f"{self._base}/auth/v1/admin/users/{auth_user_id}"
        request = Request(
            url,
            method="GET",
            headers={
                "Authorization": f"Bearer {self._secret}",
                "apikey": self._secret,
            },
        )
        try:
            with urlopen(request, timeout=10) as response:  # noqa: S310
                payload = json.loads(response.read().decode("utf-8"))
                if not isinstance(payload, dict):
                    raise AuthBootstrapError("Invalid Supabase admin response payload")
                return payload
        except HTTPError as exc:
            raise AuthBootstrapError(
                f"Supabase admin request failed: {exc.code}"
            ) from exc
        except URLError as exc:
            raise AuthBootstrapError("Supabase admin request failed") from exc
        except TimeoutError as exc:
            raise AuthBootstrapError("Supabase admin request timed out") from exc


class AuthBootstrapService:
    _UNIQUE_VIOLATION_SQLSTATE = "23505"
    _AUTH_USER_ID_CONSTRAINT_MARKERS = (
        "users_auth_user_id_key",
        "users.auth_user_id",
        "(auth_user_id)",
    )
    _USERNAME_CONSTRAINT_MARKERS = (
        "ix_users_username",
        "users_username_key",
        "uq_users_username",
        "users.username",
        "(username)",
    )
    _EMAIL_CONSTRAINT_MARKERS = (
        "users_email_key",
        "uq_users_email",
        "users.email",
        "(email)",
    )

    def __init__(self, db: AsyncSession, settings: Settings):
        self.db = db
        self.settings = settings
        self.admin_client = SupabaseAdminClient(settings)

    async def get_or_create_user(self, identity: AuthIdentity) -> User:
        """Resolve app user by Supabase auth id; bootstrap row on first authenticated call."""
        email = identity.email.strip().lower()
        self._enforce_ufl_email(email)

        existing = await self._get_by_auth_user_id(identity.auth_user_id)
        if existing is not None:
            return existing

        admin_user = self.admin_client.get_user(identity.auth_user_id)
        self._enforce_email_confirmed(identity=identity, admin_user=admin_user)

        metadata = self._extract_metadata(admin_user)
        username = validate_username(
            identity.username
            or self._read_str(metadata, "username")
            or self._derive_username_from_email(email)
        )
        full_name = self._normalize_full_name(
            identity.full_name or self._read_str(metadata, "full_name")
        )

        user = User(  # pyright: ignore[reportCallIssue]
            auth_user_id=identity.auth_user_id,
            email=email,
            username=username,
            full_name=full_name,
            role=USER_ROLE_STUDENT,
        )
        try:
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except IntegrityError as exc:
            await self.db.rollback()
            error_type = self._classify_unique_integrity_error(exc)
            if error_type in {"auth_user_id", "email"}:
                existing = await self._get_by_auth_user_id(identity.auth_user_id)
                if existing is not None:
                    return existing
            if error_type == "username":
                raise UsernameConflictError("username_taken") from exc
            raise
        except Exception:
            await self.db.rollback()
            raise

    async def _get_by_auth_user_id(self, auth_user_id: UUID) -> User | None:
        result = await self.db.exec(
            select(User).where(User.auth_user_id == auth_user_id)
        )
        return result.one_or_none()

    @staticmethod
    def _read_str(payload: dict[str, Any], key: str) -> str | None:
        value = payload.get(key)
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _normalize_full_name(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _derive_username_from_email(email: str) -> str:
        # Fallback only when upstream metadata is unexpectedly absent.
        return email.split("@", maxsplit=1)[0]

    @staticmethod
    def _extract_metadata(admin_user: dict[str, Any]) -> dict[str, Any]:
        metadata = admin_user.get("user_metadata", {})
        if isinstance(metadata, dict):
            return metadata
        return {}

    @staticmethod
    def _is_email_confirmed(admin_user: dict[str, Any]) -> bool:
        value = admin_user.get("email_confirmed_at")
        return isinstance(value, str) and bool(value.strip())

    def _enforce_email_confirmed(
        self, *, identity: AuthIdentity, admin_user: dict[str, Any]
    ) -> None:
        if identity.email_confirmed is True:
            return
        if self._is_email_confirmed(admin_user):
            return
        raise EmailPolicyError("Email confirmation required")

    @staticmethod
    def _enforce_ufl_email(email: str) -> None:
        if not email.endswith("@ufl.edu"):
            raise EmailPolicyError("Only @ufl.edu accounts are allowed")

    @staticmethod
    def _classify_unique_integrity_error(
        exc: IntegrityError,
    ) -> str:
        orig = getattr(exc, "orig", exc)
        raw = str(orig).lower()
        pgcode = getattr(orig, "pgcode", None) or getattr(orig, "sqlstate", None)
        constraint_name = getattr(getattr(orig, "diag", None), "constraint_name", None)

        is_unique_violation = (
            pgcode == AuthBootstrapService._UNIQUE_VIOLATION_SQLSTATE
            or "unique constraint" in raw
            or "is not unique" in raw
        )
        if not is_unique_violation:
            return "other"

        normalized_constraint_name = (
            str(constraint_name).lower() if constraint_name is not None else ""
        )
        markers = " ".join((normalized_constraint_name, raw))
        if any(
            marker in markers
            for marker in AuthBootstrapService._AUTH_USER_ID_CONSTRAINT_MARKERS
        ):
            return "auth_user_id"
        if any(
            marker in markers
            for marker in AuthBootstrapService._USERNAME_CONSTRAINT_MARKERS
        ):
            return "username"
        if any(
            marker in markers
            for marker in AuthBootstrapService._EMAIL_CONSTRAINT_MARKERS
        ):
            return "email"
        return "other"
