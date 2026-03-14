import firebase_admin
from firebase_admin import credentials, firestore_async
from typing import AsyncGenerator

from config import app_config

# Initialize Firebase Admin SDK
try:
    cred = credentials.Certificate(app_config.firebase_credentials_path)
    firebase_admin.initialize_app(cred, {"projectId": app_config.firebase_project_id})
except Exception as e:
    print(f"⚠️  Firebase initialization error: {e}")
    print("Make sure FIREBASE_CREDENTIALS_PATH points to a valid serviceAccountKey.json")
    raise


async def get_db():
    """
    Dependency for FastAPI to inject Firestore client.
    Returns an async Firestore client.
    """
    db = firestore_async.client()
    try:
        yield db
    finally:
        pass  # Firestore client doesn't need explicit closing


def get_firestore_client():
    """Get Firestore client instance (sync version if needed)"""
    return firestore_async.client()
