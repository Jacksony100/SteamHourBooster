from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe

import jwt
from app.core.config import get_settings
from cryptography.fernet import Fernet
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def new_session_id() -> str:
    return token_urlsafe(32)


def create_session_token(user_id: int, session_id: str) -> str:
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.session_ttl_minutes)
    return jwt.encode({"sub": str(user_id), "sid": session_id, "exp": expires_at}, settings.secret_key, algorithm="HS256")


def decode_session_payload(token: str) -> dict | None:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except Exception:
        return None


def decode_session_token(token: str) -> int | None:
    payload = decode_session_payload(token)
    if payload:
        return int(payload["sub"])
    return None


def new_csrf_token() -> str:
    return token_urlsafe(32)


class EncryptionService:
    def __init__(self) -> None:
        self._fernet = Fernet(get_settings().encryption_key.encode("utf-8"))

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, token: str) -> str:
        return self._fernet.decrypt(token.encode("utf-8")).decode("utf-8")


encryption_service = EncryptionService()
