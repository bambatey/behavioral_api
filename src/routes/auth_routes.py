import os
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from firebase_admin import auth as firebase_auth
from src.utils import create_access_token
import requests
from src.config import app_config

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
        api_key = os.getenv('FIREBASE_API_KEY')

        # Check if API key is set
        if not api_key:
            print(f"❌ FIREBASE_API_KEY is not set in .env file")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server configuration error",
            )

        # Firebase signInWithPassword endpoint
        firebase_rest_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"

        payload = {
            "email": email,
            "password": request.password,
            "returnSecureToken": True
        }

        print(f"🔐 Authenticating user: {email}")
        response = requests.post(firebase_rest_url, json=payload, timeout=10)

        print(f"Firebase response status: {response.status_code}")
        response_data = response.json() if response.text else {}
        print(f"Firebase response body: {response_data}")

        # Check for errors - Firebase can return errors with status 200
        if response.status_code != 200 or "error" in response_data:
            error_message = response_data.get("error", {}).get("message", "Unknown error") if isinstance(response_data.get("error"), dict) else response_data.get("error", "Unknown error")
            print(f"❌ Firebase auth failed for {email}: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Verify response contains idToken (successful authentication)
        if "idToken" not in response_data:
            print(f"❌ Firebase response missing idToken for {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Password verified - create JWT token
        print(f"✅ {email} authenticated successfully")
        access_token = create_access_token(email)

        return LoginResponse(
            access_token=access_token,
            email=email,
        )
    except HTTPException:
        raise
    except requests.RequestException as e:
        print(f"❌ Firebase REST API request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        )
    except Exception as e:
        print(f"❌ Login error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        )

