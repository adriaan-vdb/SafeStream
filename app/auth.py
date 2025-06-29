"""SafeStream JWT Authentication Module.

Implements secure, stateless user authentication using JWT tokens with SQLAlchemy database.
Database-only implementation with no legacy JSON file support.
"""

import os
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.db import async_session
from app.services import database as db_service

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


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


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


async def get_user(username: str) -> UserInDB | None:
    """Get user from database."""
    async with async_session() as session:
        db_user = await db_service.get_user_by_username(session, username)
        if db_user:
            return UserInDB(
                username=db_user.username,
                email=db_user.email,
                disabled=not db_user.is_active,
                hashed_password=db_user.hashed_password,
            )
    return None


async def authenticate_user(username: str, password: str) -> UserInDB | None:
    """Authenticate user with username and password."""
    async with async_session() as session:
        db_user = await db_service.authenticate_user(session, username, password)
        if db_user:
            return UserInDB(
                username=db_user.username,
                email=db_user.email,
                disabled=not db_user.is_active,
                hashed_password=db_user.hashed_password,
            )
    return None


async def create_user(
    username: str,
    password: str,
    email: str | None = None,
) -> UserInDB:
    """Create a new user in database."""
    async with async_session() as session:
        # Check if user exists in database
        existing_user = await db_service.get_user_by_username(session, username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

        # Create user in database
        hashed_password = get_password_hash(password)
        db_user = await db_service.create_user(
            session, username, email, hashed_password
        )

        return UserInDB(
            username=db_user.username,
            email=db_user.email,
            disabled=not db_user.is_active,
            hashed_password=db_user.hashed_password,
        )


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

    user = await get_user(username=token_data.username)
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


async def get_user_by_token(token: str) -> User | None:
    """Get user from JWT token without dependency injection."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return await get_user(username=username)
    except JWTError:
        return None
