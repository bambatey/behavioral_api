import firebase_admin
from firebase_admin import credentials, firestore_async
from typing import AsyncGenerator

from config import app_config

# Initialize Firebase Admin SDK from environment variables
try:
    # Build credentials dict from parsed Firebase config
    creds_dict = {
        "type": app_config.firebase.type,
        "project_id": app_config.firebase.project_id,
        "private_key_id": app_config.firebase.private_key_id,
        "private_key": app_config.firebase.private_key,
        "client_email": app_config.firebase.client_email,
        "client_id": app_config.firebase.client_id,
        "auth_uri": app_config.firebase.auth_uri,
        "token_uri": app_config.firebase.token_uri,
        "auth_provider_x509_cert_url": app_config.firebase.auth_provider_x509_cert_url,
        "client_x509_cert_url": app_config.firebase.client_x509_cert_url,
        "universe_domain": app_config.firebase.universe_domain,
    }

    cred = credentials.Certificate(creds_dict)
    firebase_admin.initialize_app(cred, {"projectId": app_config.firebase.project_id})
    print("✓ Firebase initialized successfully from .env")
except Exception as e:
    print(f"⚠️  Firebase initialization error: {e}")
    print("Make sure FIREBASE_CREDENTIALS is set correctly in .env")
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
