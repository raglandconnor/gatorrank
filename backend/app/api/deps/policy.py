from collections.abc import Callable
from typing import NoReturn

from fastapi import HTTPException, status

from app.policy.roles import PolicyDeniedError


def require_policy(check: Callable[[], None], *, detail: str) -> None:
    """Execute a policy guard and raise a standardized forbidden response on denial."""
    try:
        check()
    except PolicyDeniedError as exc:
        raise_policy_forbidden(detail=detail, exc=exc)


def raise_policy_forbidden(*, detail: str, exc: PolicyDeniedError) -> NoReturn:
    """Raise a forbidden HTTP error from a policy denial exception."""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail,
    ) from exc
