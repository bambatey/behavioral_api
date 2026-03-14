from fastapi import HTTPException, Header, status
from config import app_config
from utils import verify_access_token, get_email_from_token


async def verify_jwt_token(authorization: str = Header(...)) -> dict:
    """
    Dependency for verifying JWT access tokens.
    Admin authorization should be managed through Firebase custom claims.

    Args:
        authorization: Authorization header containing "Bearer <jwt_token>"

    Returns:
        dict: Decoded token data

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Extract token from "Bearer <token>" format
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
            )

        token = authorization.split(" ")[1]

        # Verify JWT token
        payload = verify_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        return payload
    except HTTPException:
        raise
    except Exception as e:
        print(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed",
        )
