"""
Authentication service for JWT token handling
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from models.database import User

logger = logging.getLogger(__name__)
settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token

    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token

    Args:
        data: Data to encode in the token

    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token

    Args:
        token: JWT token to decode

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get a user by email address

    Args:
        db: Database session
        email: User's email address

    Returns:
        User object or None
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get a user by ID

    Args:
        db: Database session
        user_id: User's ID

    Returns:
        User object or None
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Authenticate a user with email and password

    Args:
        db: Database session
        email: User's email
        password: User's password

    Returns:
        User object if authenticated, None otherwise
    """
    user = await get_user_by_email(db, email)

    if not user:
        logger.info(f"Authentication failed: user not found for email {email}")
        return None

    if not verify_password(password, user.hashed_password):
        logger.info(f"Authentication failed: invalid password for email {email}")
        return None

    if not user.is_active:
        logger.info(f"Authentication failed: user {email} is inactive")
        return None

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    logger.info(f"User {email} authenticated successfully")
    return user


async def create_user(
    db: AsyncSession,
    email: str,
    password: str,
    full_name: Optional[str] = None,
    is_superuser: bool = False
) -> User:
    """Create a new user

    Args:
        db: Database session
        email: User's email
        password: User's password
        full_name: User's full name
        is_superuser: Whether user is a superuser

    Returns:
        Created user object
    """
    hashed_password = get_password_hash(password)

    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        is_superuser=is_superuser
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"Created new user: {email}")
    return user
