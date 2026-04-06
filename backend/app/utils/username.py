import re

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 32
USERNAME_PATTERN = re.compile(r"^[a-z0-9_-]+$")
RESERVED_USERNAMES = {
    "admin",
    "api",
    "auth",
    "by-username",
    "help",
    "login",
    "me",
    "root",
    "signup",
    "support",
}


def normalize_username(value: str) -> str:
    return value.strip().lower()


def validate_username(value: str) -> str:
    normalized = normalize_username(value)
    if not (USERNAME_MIN_LENGTH <= len(normalized) <= USERNAME_MAX_LENGTH):
        raise ValueError(
            f"Username must be between {USERNAME_MIN_LENGTH} and "
            f"{USERNAME_MAX_LENGTH} characters"
        )
    if not USERNAME_PATTERN.fullmatch(normalized):
        raise ValueError(
            "Username may contain only lowercase letters, numbers, `_`, and `-`"
        )
    if normalized in RESERVED_USERNAMES:
        raise ValueError("Username is reserved")
    return normalized
