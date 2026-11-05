from collections import defaultdict
from datetime import datetime, timedelta, timezone
import logging
import os
from pathlib import Path
from threading import Lock
import time
from typing import Optional, Tuple
import uuid

from dotenv import load_dotenv
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas

logger = logging.getLogger("security")

# Locate and load the .env file
env_path = Path(__file__).resolve().parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).resolve().parent.parent / ".env"

load_dotenv(dotenv_path=env_path)

SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_jwt_key_page_to_voice_2026")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
JWT_ISSUER = "page-to-voice"
JWT_AUDIENCE = "page-to-voice-api"

# Bcrypt context with 12 rounds for enhanced security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Pre-computed bcrypt hash for timing attack mitigation (cost 12)
DUMMY_BCRYPT_HASH = "$2b$12$K4.Q9y9rPqC50EwNq2nOfeO4vJ7F5P7sL2rM5rO5K9X6gY0Y1Z2O2"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the stored bcrypt hash with fallback support."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        import bcrypt
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:72],
            hashed_password.encode("utf-8"),
        )


def get_password_hash(password: str) -> str:
    """Generate a bcrypt hash from a plain password with cost factor 12."""
    try:
        return pwd_context.hash(password)
    except Exception:
        import bcrypt
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8")[:72], salt).decode("utf-8")


def verify_dummy_password(plain_password: str) -> None:
    """Run password verification against a dummy hash to prevent timing attacks."""
    try:
        verify_password(plain_password, DUMMY_BCRYPT_HASH)
    except Exception:
        pass


class LoginRateLimiter:
    """In-memory rate limiter to prevent brute-force and credential stuffing attacks."""

    def __init__(self, max_attempts: int = 5, lockout_seconds: int = 900):
        self.max_attempts = max_attempts
        self.lockout_seconds = lockout_seconds
        self._failures = defaultdict(list)
        self._lockouts = {}
        self._lock = Lock()

    def _cleanup_old_attempts(self, key: str, now: float):
        self._failures[key] = [
            t for t in self._failures[key] if now - t < self.lockout_seconds
        ]

    def is_locked(self, key: str) -> Tuple[bool, int]:
        """Check if an IP or user identifier is currently locked out."""
        now = time.time()
        with self._lock:
            if key in self._lockouts:
                remaining = int(self._lockouts[key] - now)
                if remaining > 0:
                    return True, remaining
                del self._lockouts[key]

            self._cleanup_old_attempts(key, now)
            if len(self._failures[key]) >= self.max_attempts:
                self._lockouts[key] = now + self.lockout_seconds
                del self._failures[key]
                return True, self.lockout_seconds
            return False, 0

    def record_failure(self, key: str) -> Tuple[bool, int]:
        """Record a failed login attempt. Returns (is_locked, remaining_seconds)."""
        now = time.time()
        with self._lock:
            self._failures[key].append(now)
            if len(self._failures[key]) >= self.max_attempts:
                self._lockouts[key] = now + self.lockout_seconds
                del self._failures[key]
                return True, self.lockout_seconds
            return False, 0

    def record_success(self, key: str) -> None:
        """Reset failures and lockouts for a key upon successful login."""
        with self._lock:
            self._failures.pop(key, None)
            self._lockouts.pop(key, None)


# Global login rate limiter instance
login_rate_limiter = LoginRateLimiter(max_attempts=5, lockout_seconds=900)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> Tuple[str, int]:
    """Generate a hardened JWT access token containing iat, nbf, iss, aud, jti, and type claims."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
        expires_in = int(expires_delta.total_seconds())
    else:
        expires_in = ACCESS_TOKEN_EXPIRE_MINUTES * 60
        expire = now + timedelta(seconds=expires_in)

    to_encode.update({
        "exp": expire,
        "iat": now,
        "nbf": now,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "jti": uuid.uuid4().hex,
        "token_type": "access",
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, expires_in


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """FastAPI dependency to validate JWT claims and extract active user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
        )
        if payload.get("token_type") != "access":
            raise credentials_exception

        email: Optional[str] = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email, role=payload.get("role"))
    except InvalidTokenError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive or suspended",
        )
    return user
