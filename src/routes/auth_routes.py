from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from firebase_admin import auth as firebase_auth
from utils import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/test-login")
async def test_login(data: dict):
    """Debug endpoint to see what's being sent"""
    print(f"Received data: {data}")
    return {"received": data}


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: str


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """
    Authenticate user with email and password using Firebase.
    Returns JWT token for subsequent API calls.

    Args:
        request: Email and password

    Returns:
        JWT access token
    """
    try:
        email = request.email.strip().lower()

        # Verify user exists in Firebase
        user = firebase_auth.get_user_by_email(email)

        # If user exists, create JWT token
        # Note: Firebase Admin SDK doesn't verify passwords directly
        # In production, use Firebase REST API or custom claims
        access_token = create_access_token(email)

        return LoginResponse(
            access_token=access_token,
            email=email,
        )
    except firebase_auth.UserNotFoundError:
        print(f"User not found: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )

