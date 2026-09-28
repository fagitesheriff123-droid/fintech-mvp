import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext

ENV = os.getenv("ENV", "development")
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if ENV == "development":
        SECRET_KEY = "dev-secret-change-me"  # fine locally, never in prod
    else:
        raise RuntimeError(
            "SECRET_KEY env var is required outside development. "
            "Refusing to start with a guessable default in production."
        )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None


RESET_TOKEN_EXPIRE_MINUTES = 30


def generate_reset_token() -> tuple[str, str, datetime]:
    """Returns (token to email the user, hash to store in the DB, expiry).
    Only the hash is stored, so a leaked database doesn't hand out usable
    reset links (the same reasoning as never storing a plaintext password)."""
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    return token, token_hash, expires


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
