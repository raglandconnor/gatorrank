import base64
import binascii
import json
from typing import Any


class CursorError(ValueError):
    """Raised when a pagination cursor is malformed."""


def encode_cursor_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(encoded).decode("utf-8")


def decode_cursor_payload(cursor: str) -> dict[str, Any]:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("utf-8"))
        payload = json.loads(raw.decode("utf-8"))
    except (
        binascii.Error,
        ValueError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise CursorError("Invalid cursor") from exc

    if not isinstance(payload, dict):
        raise CursorError("Invalid cursor")

    return payload
