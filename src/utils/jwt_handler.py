import jwt
from datetime import datetime, timedelta
from config import app_config

SECRET_KEY = "your-secret-key-change-this-in-production"  # Should be in config
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def create_access_token(email: str) -> str:
    """
    Create a JWT access token for authenticated user.

    Args:
        email: User's email address

    Returns:
        JWT token string
    """
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode = {
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> dict | None:
    """
    Verify a JWT access token and return the payload.

    Args:
        token: JWT token string

    Returns:
        Token payload dict if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("email")
        if email is None:
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_email_from_token(token: str) -> str | None:
    """Extract email from JWT token."""
    payload = verify_access_token(token)
    return payload.get("email") if payload else None
