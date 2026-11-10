import base64
import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4


@dataclass(frozen=True)
class AuthenticatedUser:
    id: UUID
    tenant_id: UUID
    email: str
    role: str


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return f"{base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        salt_text, digest_text = encoded.split("$", 1)
        salt = base64.urlsafe_b64decode(salt_text.encode())
        expected = base64.urlsafe_b64decode(digest_text.encode())
    except (ValueError, UnicodeDecodeError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return hmac.compare_digest(actual, expected)


def issue_token(user_id: UUID) -> tuple[str, datetime]:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=12)
    return token, expires_at


def auth_enabled() -> bool:
    return os.getenv("CONSULTAI_AUTH_ENABLED", "false").lower() == "true"


def new_identity() -> tuple[UUID, UUID]:
    return uuid4(), uuid4()
