"""SafeStream JWT Authentication Module.

Implements secure, stateless user authentication using JWT tokens.
Supports login, registration, and protected access to chat and API features.
"""

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# User storage file (can be overridden for tests)
USERS_FILE = Path(os.getenv("SAFESTREAM_USERS_FILE", "users.json"))


class User(BaseModel):
    """User model for authentication."""

    username: str
    email: str | None = None
    disabled: bool = False


class UserInDB(User):
    """User model with hashed password."""

    hashed_password: str


class Token(BaseModel):
    """JWT token response model."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """JWT token payload data."""

    username: str | None = None


class UserCreate(BaseModel):
    """User registration model."""

    username: str
    password: str
    email: str | None = None


def load_users(users_file: Path = USERS_FILE) -> dict[str, UserInDB]:
    """Load users from JSON file."""
    if not users_file.exists():
        return {}
    try:
        with open(users_file, encoding="utf-8") as f:
            data = json.load(f)
            return {
                username: UserInDB(**user_data) for username, user_data in data.items()
            }
    except (json.JSONDecodeError, KeyError, ValueError):
        return {}


def save_users(users: dict[str, UserInDB], users_file: Path = USERS_FILE) -> None:
    """Save users to JSON file."""
    users_file.parent.mkdir(exist_ok=True)
    data = {username: user.model_dump() for username, user in users.items()}
    with open(users_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def get_user(username: str, users_file: Path = USERS_FILE) -> UserInDB | None:
    """Get user by username."""
    users = load_users(users_file)
    return users.get(username)


def authenticate_user(
    username: str, password: str, users_file: Path = USERS_FILE
) -> UserInDB | None:
    """Authenticate user with username and password."""
    user = get_user(username, users_file)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as err:
        raise credentials_exception from err

    if token_data.username is None:
        raise credentials_exception

    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user (not disabled)."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def create_user(
    username: str,
    password: str,
    email: str | None = None,
    users_file: Path = USERS_FILE,
) -> UserInDB:
    """Create a new user."""
    users = load_users(users_file)

    if username in users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    hashed_password = get_password_hash(password)
    user = UserInDB(username=username, hashed_password=hashed_password, email=email)

    users[username] = user
    save_users(users, users_file)
    return user


def get_user_by_token(token: str, users_file: Path = USERS_FILE) -> User | None:
    """Get user from JWT token without dependency injection."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return get_user(username=username, users_file=users_file)
    except JWTError:
        return None
